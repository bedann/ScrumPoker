from firebase_admin import firestore
import json
import os

settings = None


def read_settings(key):
    global settings
    if settings:
        return settings[key]
    elif os.path.exists('settings.json'):
        with open('settings.json', 'r') as openfile:
            settings = json.load(openfile)
            return settings[key]
    else:
        with open('settings.json', 'w+') as openfile:
            settings = {"email": None}
            json.dump(settings, openfile)
    return None


def write_settings(key, value):
    global settings
    settings[key] = value
    with open('settings.json', 'w') as outfile:
        json.dump(settings, outfile)


def ref_to_dict(ref: firestore.firestore.DocumentSnapshot):
    return {**ref.to_dict(), **{"id": ref.id}}

