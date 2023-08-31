
def find_crm_entities_by_site(but, domain):
    methods = [
        ('LEAD', 'crm.lead.list', {'filter': {'WEB': domain}}),
        ('LEAD_HTTP', 'crm.lead.list', {'filter': {'WEB': 'http://{}'.format(domain)}}),
        ('LEAD_HTTPS', 'crm.lead.list', {'filter': {'WEB': 'https://{}'.format(domain)}}),

        ('COMPANY', 'crm.company.list', {'filter': {'WEB': domain}}),
        ('COMPANY_HTTP', 'crm.company.list', {'filter': {'WEB': 'http://{}'.format(domain)}}),
        ('COMPANY_HTTPS', 'crm.company.list', {'filter': {'WEB': 'https://{}'.format(domain)}}),

        ('CONTACT', 'crm.contact.list', {'filter': {'WEB': domain}}),
        ('CONTACT_HTTP', 'crm.contact.list', {'filter': {'WEB': 'http://{}'.format(domain)}}),
        ('CONTACT_HTTPS', 'crm.contact.list', {'filter': {'WEB': 'https://{}'.format(domain)}}),
    ]

    resp = but.batch_api_call(methods)
    response = {'result': {}}
    if resp['LEAD'].get('result'):
        response['result']['LEAD'] = [int(x['ID']) for x in resp['LEAD'].get('result')]
    if resp['LEAD_HTTP'].get('result'):
        response['result']['LEAD'] = [int(x['ID']) for x in resp['LEAD_HTTP'].get('result')]
    if resp['LEAD_HTTPS'].get('result'):
        response['result']['LEAD'] = [int(x['ID']) for x in resp['LEAD_HTTPS'].get('result')]
    if resp['COMPANY'].get('result'):
        response['result']['COMPANY'] = [int(x['ID']) for x in resp['COMPANY'].get('result')]
    if resp['COMPANY_HTTP'].get('result'):
        response['result']['COMPANY'] = [int(x['ID']) for x in resp['COMPANY_HTTP'].get('result')]
    if resp['COMPANY_HTTPS'].get('result'):
        response['result']['COMPANY'] = [int(x['ID']) for x in resp['COMPANY_HTTPS'].get('result')]
    if resp['CONTACT'].get('result'):
        response['result']['CONTACT'] = [int(x['ID']) for x in resp['CONTACT'].get('result')]
    if resp['CONTACT_HTTP'].get('result'):
        response['result']['CONTACT'] = [int(x['ID']) for x in resp['CONTACT_HTTP'].get('result')]
    if resp['CONTACT_HTTPS'].get('result'):
        response['result']['CONTACT'] = [int(x['ID']) for x in resp['CONTACT_HTTPS'].get('result')]

    # возвращает как при  crm.duplicate.findbycomm'
    return response



#
def find_crm_entities(but ):
    pass