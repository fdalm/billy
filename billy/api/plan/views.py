from __future__ import unicode_literals

import transaction as db_transaction
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPBadRequest

from billy.models.plan import PlanModel 
from billy.models.customer import CustomerModel 
from billy.models.subscription import SubscriptionModel 
from billy.models.transaction import TransactionModel 
from billy.api.auth import auth_api_key
from billy.api.utils import validate_form
from billy.api.utils import list_by_ancestor
from .forms import PlanCreateForm


def get_and_check_plan(request, company):
    """Get and check permission to access a plan

    """
    model = request.model_factory.create_plan_model()
    guid = request.matchdict['plan_guid']
    plan = model.get(guid)
    if plan is None:
        raise HTTPNotFound('No such plan {}'.format(guid))
    if plan.company_guid != company.guid:
        raise HTTPForbidden('You have no permission to access plan {}'
                            .format(guid))
    return plan


@view_config(route_name='plan_list', 
             request_method='GET', 
             renderer='json')
def plan_list_get(request):
    """Get and return plans

    """
    company = auth_api_key(request)
    return list_by_ancestor(request, PlanModel, company)


@view_config(route_name='plan_customer_list', 
             request_method='GET', 
             renderer='json')
def plan_customer_list_get(request):
    """Get and return customer list under the plan

    """
    company = auth_api_key(request)
    plan = get_and_check_plan(request, company)
    return list_by_ancestor(request, CustomerModel, plan)


@view_config(route_name='plan_subscription_list', 
             request_method='GET', 
             renderer='json')
def plan_subscription_list_get(request):
    """Get and return subscription list under the plan

    """
    company = auth_api_key(request)
    plan = get_and_check_plan(request, company)
    return list_by_ancestor(request, SubscriptionModel, plan)


@view_config(route_name='plan_transaction_list', 
             request_method='GET', 
             renderer='json')
def plan_transaction_list_get(request):
    """Get and return subscription list under the plan

    """
    company = auth_api_key(request)
    plan = get_and_check_plan(request, company)
    return list_by_ancestor(request, TransactionModel, plan)


@view_config(route_name='plan_list', 
             request_method='POST', 
             renderer='json')
def plan_list_post(request):
    """Create a new plan 

    """
    company = auth_api_key(request)
    form = validate_form(PlanCreateForm, request)
    
    plan_type = form.data['plan_type']
    amount = form.data['amount']
    frequency = form.data['frequency']
    interval = form.data['interval']
    if interval is None:
        interval = 1

    # TODO: make sure user cannot create a post to a deleted company

    model = request.model_factory.create_plan_model()
    type_map = dict(
        charge=model.TYPE_CHARGE,
        payout=model.TYPE_PAYOUT,
    )
    plan_type = type_map[plan_type]
    freq_map = dict(
        daily=model.FREQ_DAILY,
        weekly=model.FREQ_WEEKLY,
        monthly=model.FREQ_MONTHLY,
        yearly=model.FREQ_YEARLY,
    )
    frequency = freq_map[frequency]

    with db_transaction.manager:
        plan = model.create(
            company=company, 
            plan_type=plan_type,
            amount=amount, 
            frequency=frequency, 
            interval=interval, 
        )
    return plan 


@view_config(route_name='plan', 
             request_method='GET', 
             renderer='json')
def plan_get(request):
    """Get and return a plan 

    """
    company = auth_api_key(request)
    plan = get_and_check_plan(request, company)
    return plan 


@view_config(route_name='plan', 
             request_method='DELETE', 
             renderer='json')
def plan_delete(request):
    """Delete a plan

    """
    company = auth_api_key(request)
    model = request.model_factory.create_plan_model()
    plan = get_and_check_plan(request, company)
    if plan.deleted:
        return HTTPBadRequest('Plan {} was already deleted'.format(plan.guid))
    with db_transaction.manager:
        model.delete(plan)
    return plan 
