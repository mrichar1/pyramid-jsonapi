import pyramid_jsonapi.workflow as wf
import sqlalchemy

from itertools import islice
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
)

stages = (
    'alter_query',
    'alter_result',
    'alter_related_query',
    'alter_related_result',
    'alter_results',
)


def workflow(view, stages):
    query = view.base_collection_query()
    query = view.query_add_sorting(query)
    query = view.query_add_filtering(query)
    qinfo = view.collection_query_info(view.request)
    limit = qinfo['page[limit]']

    # If there is any chance that the code might alter the number of results
    # after they come from the database then we can't rely on LIMIT and COUNT
    # at the database end, so these have been disabled. They might return
    # if a suitable flag is introduced.
    # try:
    #     count = query.count()
    # except sqlalchemy.exc.ProgrammingError:
    #     raise HTTPInternalServerError(
    #         'An error occurred querying the database. Server logs may have details.'
    #     )
    # query = query.limit(limit)
    # query = query.offset(qinfo['page[offset]'])

    query = wf.execute_stage(
        view, stages, 'alter_query', query
    )

    # Get the direct results from this collection (no related objects yet).
    # Stage 'alter_result' will run on each object.
    objects_iterator = wf.loop.altered_objects_iterator(
        view, stages, 'alter_result', query
    )
    # Only do paging the slow way if page[offset] is explicitly specified in the
    # request.
    offset_count = 0
    if 'page[offset]' in view.request.params:
        offset_count = sum(1 for _ in islice(objects_iterator, qinfo['page[offset]']))
    objects = list(islice(objects_iterator, limit))
    count = None
    if(qinfo['pj_include_count']):
        count = offset_count + len(objects) + sum(1 for _ in objects_iterator)
    results = wf.Results(
        view,
        objects=objects,
        many=True,
        is_top=True,
        count=count,
        limit=limit
    )

    # Fill the relationships with related objects.
    # Stage 'alter_related_result' will run on each object.
    for res_obj in results.objects:
        wf.loop.fill_result_object_related(res_obj, stages)

    # A chance to alter the complete set of results before they are serialised.
    results = wf.execute_stage(view, stages, 'alter_results', results)

    return results.serialise()
