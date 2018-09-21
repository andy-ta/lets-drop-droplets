import argparse
import requests
import json
import time

parser = argparse.ArgumentParser(description='Kills or creates a DigitalOcean Droplet with a snapshot.\n'
                                             'It also assigns the first floating ip it finds to the droplet.\n'
                                             'Useful for saving on DigitalOcean credits when you\'re not working.')
parser.add_argument('-k', action='store_true', help='opposite of creating, therefore killing a droplet')
parser.add_argument('token', help='your authorization token for the DigitalOcean API')
parser.add_argument('-n', '--name', default='cvas', help='the name of the droplet (default: cvas)')
parser.add_argument('-r', '--region', default='tor1',
                    help='unique slug identifier for the region that you wish to deploy in (default: tor1)')
parser.add_argument('-s', '--size', default='s-2vcpu-4gb', help='unique slug identifier for the size '
                                                                '(default: s-2vcpu-4gb')

args = parser.parse_args()

headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + args.token}


def fetch_droplet():
    url = 'https://api.digitalocean.com/v2/droplets'

    r = requests.get(url, headers=headers)

    print('Status of snapshot fetch: ' + str(r.status_code))
    droplets = r.content
    dl_id = None
    for droplet in json.loads(droplets)['droplets']:
        if droplet['name'] == args.name:
            dl_id = droplet['id']
    if dl_id:
        return dl_id
    else:
        raise Exception('Failed to find droplet.')


def shutdown(dl_id):
    url = 'https://api.digitalocean.com/v2/droplets/' + str(dl_id) + '/actions'

    payload = {
        'type': 'shutdown'
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    print('Status of shutdown: ' + str(r.status_code))

    payload = {
        'type': 'power_off'
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    print('Status of power off: ' + str(r.status_code))

    return assert_success(r.status_code)


def snap(dl_id):
    url = 'https://api.digitalocean.com/v2/droplets/' + str(dl_id) + '/actions'

    payload = {
        'type': 'snapshot',
        'name': 'ldd-snapshot'
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    print('Status of snapshot creation: ' + str(r.status_code))

    return assert_success(r.status_code)


def kill(dl_id):
    url = 'https://api.digitalocean.com/v2/droplets/' + str(dl_id)

    r = requests.delete(url, headers=headers)

    print('Status of droplet after assassination attempt: ' + str(r.status_code))

    return assert_success(r.status_code)


def fetch_image():
    url = 'https://api.digitalocean.com/v2/images?private=true'

    r = requests.get(url, headers=headers)

    print('Status of snapshot fetch: ' + str(r.status_code))

    return r.content


def delete_image(image_id):
    url = 'https://api.digitalocean.com/v2/images/' + str(image_id)

    r = requests.delete(url, headers=headers)

    print('Status of image deletion: ' + str(r.status_code))

    return assert_success(r.status_code)


def birth(images):
    image_id = None
    for image in json.loads(images)['images']:
        if image['name'] == 'ldd-snapshot':
            image_id = image['id']
    if image_id:
        url = 'https://api.digitalocean.com/v2/droplets'

        payload = {
            'name': args.name,
            'region': args.region,
            'size': args.size,
            'image': image_id
        }

        r = requests.post(url, data=json.dumps(payload), headers=headers)
        print('Status of creation: ' + str(r.status_code))

        if assert_success(r.status_code):
            return delete_image(image_id)
        else:
            return False
    else:
        raise Exception('Failed to find snapshot named \'ldd-snapshot\'.')


def floating_ip(dl_id):
    url = 'https://api.digitalocean.com/v2/floating_ips'
    r = requests.get(url, headers=headers)

    print('Status of floating ip fetch: ' + str(r.status_code))

    if assert_success(r.status_code):
        float_ip = None
        for ip in json.loads(r.content)['floating_ips']:
            if not ip['droplet']:
                float_ip = ip['ip']
        if float_ip:
            url = 'https://api.digitalocean.com/v2/floating_ips/' + float_ip + '/actions'
            payload = {
                'type': 'assign',
                'droplet_id': dl_id
            }
        else:
            url = 'https://api.digitalocean.com/v2/floating_ips'

            payload = {
                'droplet_id': dl_id
            }

        r = requests.post(url, data=json.dumps(payload), headers=headers)

        print('Status of floating ip assignment: ' + str(r.status_code))

        return assert_success(r.status_code)
    else:
        return False


def assert_success(status_code):
    if int(status_code / 100) == 2:
        return True
    return False


if args.k:
    droplet_id = fetch_droplet()
    if shutdown(droplet_id):
        if snap(droplet_id):
            kill(droplet_id)
else:
    if birth(fetch_image()):
        print('\nPreparing to assign ip (2 mins)...')
        time.sleep(120)
        floating_ip(fetch_droplet())
