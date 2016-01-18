from datetime import timedelta, datetime

import pytz
import requests
from django.conf import settings
from django.utils.timezone import now

from insekta.remoteapi.models import VMResourceDummy


STATUS_OK = 200


class RemoteApiError(Exception):
    pass


class RemoteApiClient:
    api_version = '1.0'

    def __init__(self, base_url, auth):
        self.auth = auth
        self.api_url = base_url + self.api_version + '/'

    def start_vm_resource(self, resource_name, user):
        ret = self._make_vm_request('vm/start', resource_name, user)
        ret['expire_time'] = datetime.fromtimestamp(ret['expire_time'], pytz.UTC)
        return ret

    def stop_vm_resource(self, resource_name, user):
        return self._make_vm_request('vm/stop', resource_name, user)

    def ping_vm_resource(self, resource_name, user):
        ret = self._make_vm_request('vm/ping', resource_name, user)
        ret['expire_time'] = datetime.fromtimestamp(ret['expire_time'], pytz.UTC)
        return ret

    def get_vm_resource_status(self, resource_name, user):
        ret = self._make_vm_request('vm/status', resource_name, user, method='get')
        if ret['resource'] and ret['resource']['expire_time']:
            resource = ret['resource']
            resource['expire_time'] = datetime.fromtimestamp(resource['expire_time'], pytz.UTC)
        return ret

    def _make_vm_request(self, api_path, resource_name, user, method='post'):
        return self._make_request(api_path, {
            'resource': resource_name,
            'username': user.username
        }, method=method)

    def _make_request(self, api_path, data, method):
        if method == 'post':
            resp = requests.post(self.api_url + api_path, data=data, auth=self.auth)
        elif method == 'get':
            resp = requests.get(self.api_url + api_path, params=data, auth=self.auth)
        else:
            raise ValueError('Invalid value for method: {}'.format(method))
        if resp.status_code != STATUS_OK:
            raise RemoteApiError('{} {}. HttpCode: {}: {}'.format(
                method.upper(), api_path, resp.status_code, resp.text))
        return resp.json()


class RemoteApiClientDummy:
    def start_vm_resource(self, resource_name, user):
        vm_res = self._get_vm_resource(resource_name)
        vm_res.is_started = True
        vm_res.save()
        return {
            'id': vm_res.pk,
            'expire_time': self._get_expire_time(),
            'virtual_machines': vm_res.get_vms()
        }

    def stop_vm_resource(self, resource_name, user):
        vm_res = self._get_vm_resource(resource_name)
        vm_res.is_started = False
        vm_res.save()
        return {
            'result': 'ok'
        }

    def ping_vm_resource(self, resource_name, user):
        return {
            'result': 'ok'
        }

    def get_vm_resource_status(self, resource_name, user):
        vm_res = self._get_vm_resource(resource_name)
        if vm_res.is_started:
            status = 'running'
            resource = {
                'id': vm_res.pk,
                'expire_time': self._get_expire_time(),
                'virtual_machines': vm_res.get_vms()
            }
            vpn_ip = '10.36.42.1'
        else:
            status = 'notrunning'
            resource = None
            vpn_ip = None

        return {
            'status': status,
            'resource': resource,
            'vpn_ip': vpn_ip
        }

    def _get_expire_time(self):
        return now() + timedelta(minutes=10)

    def _get_vm_resource(self, resource_name):
        try:
            return VMResourceDummy.objects.get(resource_name=resource_name)
        except VMResourceDummy.DoesNotExist:
            raise RemoteApiError('No such vm resource: {}'.format(resource_name))


if settings.USE_REMOTE_API_DUMMY:
    remote_api = RemoteApiClientDummy()
else:
    remote_api = RemoteApiClient(settings.REMOTE_API_URL, settings.REMOTE_API_AUTH)
