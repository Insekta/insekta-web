from django.conf import settings
from django.db import models, connection
from django.utils.timezone import now

from insekta.scenarios.models import Scenario


READ_STATES = (
    ('read', 'Read questions')
)


class Question(models.Model):
    title = models.CharField(max_length=120)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    time_created = models.DateTimeField(default=now)
    scenario = models.ForeignKey(Scenario)
    is_solved = models.BooleanField(default=False, db_index=True)
    seen_by_author = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def post_answer(self, author, text, time_created=None):
        if time_created is None:
            time_created = now()
        post = Post.objects.create(question=self,
                                   author=author,
                                   text=text,
                                   time_created=time_created)
        # If the creator of the question has written a post, we want to mark
        # the question as unread for all users who participated in the
        # discussion.
        if author == self.author:
            other_posts = (Post.objects.filter(question=self, author=author)
                           .select_related('author'))
            other_authors = [other_post.author for other_post in other_posts]
            SeenQuestion.objects.filter(question=self, user__in=other_authors).delete()
        else:
            self.seen_by_author = False
            self.save()
        return post

    def mark_seen(self, user):
        if user == self.author:
            self.seen_by_author = True
            self.save()
        else:
            SeenQuestion.objects.get_or_create(question=self, user=user)

    def mark_solved(self):
        self.is_solved = True
        SeenQuestion.objects.filter(question=self).delete()
        self.save()


class Post(models.Model):
    question = models.ForeignKey(Question)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    time_created = models.DateTimeField(default=now)
    text = models.TextField()

    def __str__(self):
        return '{}: {} said: {}'.format(self.question, self.author, self.text[:80])


class SeenQuestion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    question = models.ForeignKey(Question)

    class Meta:
        unique_together = ('question', 'user')

    def __str__(self):
        return '{} helped at {}'.format(self.user, self.question)


class SupportedScenario(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='supported_scenarios')
    scenario = models.ForeignKey(Scenario)

    class Meta:
        unique_together = ('user', 'scenario')

    def __str__(self):
        return '{} supports {}'.format(self.user, self.scenario)


def get_num_unseen(user):
    sql_query = '''
    SELECT COUNT(q.id)
    FROM scenariohelp_question AS q
    LEFT JOIN scenariohelp_seenquestion AS sq ON q.id = sq.question_id
    WHERE NOT q.is_solved AND
          q.author_id <> %s AND
          sq.id IS NULL AND
          q.scenario_id IN
            (SELECT scenario_id FROM scenariohelp_supportedscenario WHERE user_id = %s)
    '''
    with connection.cursor() as c:
        c.execute(sql_query, (user.pk, user.pk))
        return c.fetchone()[0]
