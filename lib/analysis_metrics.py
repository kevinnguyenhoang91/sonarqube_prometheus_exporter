# Importing the functions from the lib.util file and the prometheus_client file.
from lib.util import get_json, sr_to_json
from prometheus_client import Enum, Gauge, Info, Summary
import json


def get_stat(metrics):
    stats = []
# Creating a list of metrics that are supported by prometheus.
    for metric in metrics:
        if metric['type'] in ['INT', 'FLOAT', 'PERCENT', 'MILLISEC', 'RATING', 'WORK_DUR']:
            g = Gauge(metric['key'], metric['name'], ['project_key', 'domain'])
        elif metric['type'] in ['BOOL']:
            g = Enum(metric['key'], metric['name'], ['project_key', 'domain'], states=['TRUE', 'FALSE'])
        elif metric['type'] in ['DATA', 'STRING']:
            g = Info(metric['key'], metric['name'], ['project_key', 'domain'])
        elif metric['type'] in ['DISTRIB']:
            g = Summary(metric['key'], metric['name'], ['project_key', 'domain'])
        elif metric['key'] == 'alert_status':
            g = Enum(metric['key'], metric['name'], ['project_key', 'domain'], states=['ERROR', 'OK'])
        else:
            print(f"Metric {metric} with type {metric['type']} and key {metric['key']} is not supported")
        stats.append({'stat':g, 'metric':metric})
    return stats

def get_value(measures):
# Getting the value of the metric.
    value = 0
    if 'value' in measures[0]:
        try:
            value = measures[0]['value']
        except (KeyError, IndexError, NameError) as error:
            raise error
    elif 'period' in measures[0]:
        try:
            value = measures[0]['period']['value']
        except (KeyError, IndexError, NameError) as error:
            raise error
    return value

def set_metrics(sonar_issue_key, sonar_issue_domain, sonar_issue_type, value, prom_metric, project_key):
# This is a function that is setting the metrics in prometheus.
    if sonar_issue_type in ['INT', 'FLOAT', 'PERCENT', 'MILLISEC', 'RATING', 'WORK_DUR']:
        prom_metric.labels(
            project_key=project_key,
            domain=sonar_issue_domain,
        ).set(value)
    elif sonar_issue_type in ['BOOL']:
        if value == 'true':
            prom_metric.labels(
                project_key=project_key,
                domain=sonar_issue_domain,
            ).state('TRUE')
        else:
            prom_metric.labels(
                project_key=project_key,
                domain=sonar_issue_domain,
            ).state('FALSE')
    elif sonar_issue_type in ['DATA', 'STRING']:
        prom_metric.labels(
            project_key=project_key,
            domain=sonar_issue_domain,
        ).info({sonar_issue_key: value})
    elif sonar_issue_type in ['DISTRIB']:
        prom_metric.labels(
            project_key=project_key,
            domain=sonar_issue_domain,
        ).observe(value)
    elif sonar_issue_key == 'alert_status':
        prom_metric.labels(
            project_key=project_key,
            domain=sonar_issue_domain,
        ).state(value)
    else:
        print(f"Metric {value} with type {sonar_issue_type} and key {sonar_issue_key} is not supported")

def common_metrics(projects, sonar, stats):
# Getting the metrics from sonarqube and setting the metrics in prometheus.
    prom_metric = stats['stat']
    sonar_metric = stats['metric']
    for p in projects:
        project_key = p['key']
        sonar_issue_key = sonar_metric['key']
        sonar_issue_domain = sonar_metric['domain']
        sonar_issue_type = sonar_metric['type']
        component = sonar.measures.get_component_with_specified_measures(component=project_key, fields="metrics", metricKeys=sonar_issue_key)
        measures = component['component']['measures']
        if len(measures) > 0:
            value = get_value(measures)
            if sonar_issue_key == 'quality_profiles':
                try:
                    parsed_value = json.loads(value)
                    value = list(set(f"{profile['name']}/{profile['language'].upper()}" for profile in parsed_value))
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON for quality_profiles: {e}")
            set_metrics(sonar_issue_key, sonar_issue_domain, sonar_issue_type, value, prom_metric, project_key)
        else:
            print('component doesn\'t have metric')

stat_rule = Gauge('stat_rule', 'Frequency of rule', ['project_key', 'rule'])
def rule_metrics(projects, sonar):
# Getting the rules from sonarqube and setting the metrics in prometheus.
    for p in projects:
        project_key = p['key']
        issues = []
        page = 1
        page_size = 100
        while True:
            response = sonar.issues.search_issues(componentKeys=project_key, p=page, ps=page_size)
            if 'issues' in response:
                issues.extend(response['issues'])
                if len(response['issues']) < page_size:
                    break
                page += 1
            else:
                break
            if page > 100:
                break
        rules = []
        for i in issues:
            rules.append(i['rule'])
        j_data = sr_to_json(rules)
        for key, value in j_data.items():
            stat_rule.labels(
                project_key=project_key,
                rule=key,
            ).set(value)

stat_event = Info('project_analyses_and_events', 'Description of project analyses', ['project_key'])
def event_metrics(projects, sonar):
# Getting the events from sonarqube and setting the metrics in prometheus.
    for p in projects:
        project_key = p['key']
        project_analyses_and_events = []
        page = 1
        page_size = 100
        while True:
            response = sonar.project_analyses.search_project_analyses_and_events(project=project_key, p=page, ps=page_size)
            if 'analyses' in response:
                project_analyses_and_events.extend(response['analyses'])
                if len(response['analyses']) < page_size:
                    break
                page += 1
            else:
                break
            if page > 100:
                break
        project_analyses_and_events = dict(analyses=project_analyses_and_events)
        for event in project_analyses_and_events['analyses']:
            event_id = get_json("key", event)
            date = get_json("date", event)
            project_version = get_json("projectVersion", event)
            value = {'event_id': event_id, 'date': date, 'project_version': project_version}
            stat_event.labels(
                project_key=project_key,
            ).info(value)
