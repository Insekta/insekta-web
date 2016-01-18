from django.db import models


class VMResourceDummy(models.Model):
    resource_name = models.CharField(max_length=80, unique=True)
    is_started = models.BooleanField(default=False)
    vm_names = models.TextField()

    def __str__(self):
        return self.resource_name

    def get_vms(self):
        vm_names = self.vm_names.split()
        vms = {}
        for i, vm_name in enumerate(vm_names):
            vms[vm_name] = {
                'ip': '10.37.42.{}'.format(i+2)
            }
        return vms