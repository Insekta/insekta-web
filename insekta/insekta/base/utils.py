def describe_allowed_markup(tag_whitelist, attr_whitelist):
    tag_desc = []
    for tag in tag_whitelist:
        if tag in attr_whitelist:
            tag_desc.append('{}[{}]'.format(tag, ', '.join(attr_whitelist[tag])))
        else:
            tag_desc.append(tag)

    return ', '.join(tag_desc)
