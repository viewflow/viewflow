/* eslint-env node */
const render = (ctx) => `
${ctx.celery ? `
from .celery import app as celery_app

__all__ = ('celery_app',)
` : ''
}
`.trimLeft();

exports.default = render;
