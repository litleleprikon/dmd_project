#!/usr/bin/env python
import json
from aiohttp import web


__author__ = 'litleleprikon'


def validate(valid_rules):
    def validator(handler):
        async def wrapper(request, *args):
            data = await request.content.read()
            try:
                parsed_data = json.loads(data.decode())
            except json.JSONDecodeError as ex:
                response = web.Response(
                    body=json.dumps({'status': 'fail', 'message': 'Data is not in JSON'}).encode(),
                    status=403
                )
                return response
            valid_data = parsed_data
            if valid_data:
                result = await handler(request, valid_data, *args)
                return result
            else:
                response = web.Response(
                    body=json.dumps({'status': 'fail', 'message': '\n'.join(valid_rules.get_errors())}).encode(),
                    status=403
                )
                return response
        return wrapper
    return validator