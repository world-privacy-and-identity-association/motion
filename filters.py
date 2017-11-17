import flask, jinja2

blueprint = flask.Blueprint('filters', __name__)

# using the decorator
@jinja2.contextfilter
@blueprint.app_template_filter()
def timestamp(context, value):
    return value.strftime("%Y-%m-%d %H:%M:%S")
