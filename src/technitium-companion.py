#!/usr/bin/python3

from datetime import datetime
import docker
import os
import re
import requests
import signal
import sys

HOST = os.environ.get("HOST", None)
API_TOKEN = os.environ.get("API_TOKEN", None)
ZONE = os.environ.get("ZONE", None)
DESTINATION = os.environ.get("DESTINATION", None)

synced_mappings = {}

def extract_domains(container):
    domains = []
    for prop in container.attrs.get(u'Config').get(u'Labels'):
        value = container.attrs.get(u'Config').get(u'Labels').get(prop)
        if re.match('traefik.*?\.rule', prop):
            if 'Host' in value:
                extracted_domains = re.findall(r"[\`\'\"]([a-zA-Z0-9\.\-]+)[\`\'\"]", value)
                for v in extracted_domains:
                    domains.append(v)
            else:
                pass
    return domains

def add_to_mappings(current_mappings, domains):
    for v in domains:
        current_mappings[v] = True

def remove_from_mappings(current_mappings, domains):
    for v in domains:
        current_mappings[v] = False


def sync_mappings(mappings):
    for k, v in mappings.items():
        current_mapping = synced_mappings.get(k)
        if current_mapping is None or (current_mapping == False and v == True):
            print("adding domain: " + k)
            requests.get(f"http://{HOST}/api/zones/records/add?token={API_TOKEN}&domain={k}&zone={ZONE}&type=CNAME&cname={DESTINATION}")
            synced_mappings[k] = True
        elif current_mapping == True and v == False:
            print("removing domain: " + k)
            synced_mappings[k] = False


def get_initial_mappings():
    mappings = {}
    for c in client.containers.list():
        add_to_mappings(mappings, extract_domains(c))
    return mappings

client = docker.from_env()

sync_mappings(get_initial_mappings())

t = datetime.now().strftime("%s")
while True:
    for event in client.events(since=t, filters={'Type': 'service', 'Action': u'update', 'status': u'start'}, decode=True):
        new_mappings = {}
        #print(event.get(u'Action'), event.get(u'status'))
        if event.get(u'status') == u'start':
            try:
                add_to_mappings(new_mappings, extract_domains(client.containers.get(event.get(u'id'))))
            except docker.errors.NotFound as e:
                pass
        elif event.get(u'status') == u'stop':
            try:
                remove_from_mappings(new_mappings, extract_domains(client.containers.get(event.get(u'id'))))
            except docker.errors.NotFound as e:
                pass
        sync_mappings(new_mappings)
