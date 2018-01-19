import argparse
import requests
import json

parser = argparse.ArgumentParser(description='Kills or creates a DigitalOccean Droplet with a snapshot.')
parser.add_argument('-o', '--o', type=str, help='opposite of creating, therefore killing a droplet with the id')
parser.add_argument('token', help='your authorization token for the DigitalOcean API')
parser.add_argument('-r', '--region', default='tor1',
                    help='unique slug identifier for the region that you wish to deploy in')
parser.add_argument('-s', '--size', default='s-4vcpu-8gb', help='unique slug identifier for the size')

args = parser.parse_args()

# TODO: Shutdown Droplet before Snapshot
# TODO: Delete snapshot after using it


def snap(droplet_id, token):
    url = 'https://api.digitalocean.com/v2/droplets/' + droplet_id + '/actions'

    payload = {
        'type': 'snapshot',
        'name': 'ldd-snapshot'
    }

    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    r = requests.post(url, data=json.dumps(payload), headers=headers)

    print('Status of snapshot creation: ' + str(r.status_code))


def kill(droplet_id, token):
    url = 'https://api.digitalocean.com/v2/droplets/' + droplet_id

    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    r = requests.delete(url, headers=headers)

    print('Status of droplet after assassination attempt: ' + str(r.status_code))


def fetch(token):
    url = 'https://api.digitalocean.com/v2/images?private=true'

    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    r = requests.get(url, headers=headers)

    print('Status of snapshot fetch ' + str(r.status_code))
    return r.content


def birth(images, token):
    image_id = ''
    for image in json.loads(images)['images']:
        if image['name'] == 'ldd-snapshot':
            image_id = image['id']
    if image_id != '':
        url = 'https://api.digitalocean.com/v2/droplets'

        payload = {
            'name': 'default',
            'region': args.region,
            'size': args.size,
            'image': image_id
        }

        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
        r = requests.post(url, data=json.dumps(payload), headers=headers)

        print('Status of creation: ' + str(r.status_code))
    else:
        raise Exception('Failed to find snapshot.')


if args.o:
    snap(args.o, args.token)
    kill(args.o, args.token)
else:
    birth(fetch(args.token), args.token)