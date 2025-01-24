from firebase_admin import firestore
import json
import os


with open('settings.json', 'w+') as openfile:
    openfile.seek(0, os.SEEK_END)
    if openfile.tell():
        openfile.seek(0)
    else:
        json.dump({"email": None}, openfile)
        openfile.seek(0)
    settings = json.load(openfile)


def read_settings(key):
    return settings[key]


def write_settings(key, value):
    settings[key] = value
    with open('settings.json', 'w') as outfile:
        json.dump(settings, outfile)


def ref_to_dict(ref: firestore.firestore.DocumentSnapshot):
    return {**ref.to_dict(), **{"id": ref.id}}

