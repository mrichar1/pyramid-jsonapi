from pyramid.settings import asbool


class RoutePattern():
    '''Hold and manipulate pyramid_jsonapi route patterns.'''

    def __init__(
        self, prefix='', sep='/',
        metadata=True,
    ):
        pass


class EndpointData():
    '''Class to hold endpoint data and utility methods.

    Arguments:
        config: A pyramid Configurator object.

    '''

    def __init__(self, config):
        self.config = config
        settings = self.config.registry.settings
        self.route_name_prefix = settings.get(
            'pyramid_jsonapi.route_name_prefix', 'pyramid_jsonapi'
        )
        self.route_name_sep = settings.get(
            'pyramid_jsonapi.route_name_sep', ':'
        )

        self.route_pattern_prefix_components = ['']
        self.route_pattern_prefix = settings.get(
            'pyramid_jsonapi.route_pattern_prefix', ''
        )
        self.metadata_endpoints = asbool(settings.get(
            'pyramid_jsonapi.metadata_endpoints', 'true'
        ))
        if self.metadata_endpoints:
            default_api_prefix = 'api'
        else:
            default_api_prefix = ''
        self.route_pattern_api_prefix = self.config.registry.settings.get(
            'pyramid_jsonapi.route_pattern_api_prefix', default_api_prefix
        )
        self.route_pattern_sep = self.config.registry.settings.get(
            'pyramid_jsonapi.route_pattern_sep', '/'
        )
        # Mapping of endpoints, http_methods and options for constructing routes and views.
        # Update this dictionary prior to calling create_jsonapi()
        # Mandatory 'endpoint' keys: http_methods
        # Optional 'endpoint' keys: route_pattern_suffix
        # Mandatory 'http_method' keys: function
        # Optional 'http_method' keys: renderer
        self.endpoints = {
            'collection': {
                'http_methods': {
                    'GET': {
                        'function': 'collection_get',
                    },
                    'POST': {
                        'function': 'collection_post',
                    },
                },
            },
            'item': {
                'route_pattern_suffix': '{id}',
                'http_methods': {
                    'DELETE': {
                        'function': 'delete',
                    },
                    'GET': {
                        'function': 'get',
                    },
                    'PATCH': {
                        'function': 'patch',
                    },
                },
            },
            'related': {
                'route_pattern_suffix': '{id}/{relationship}',
                'http_methods': {
                    'GET': {
                        'function': 'related_get',
                    },
                },
            },
            'relationships': {
                'route_pattern_suffix': '{id}/relationships/{relationship}',
                'http_methods': {
                    'DELETE': {
                        'function': 'relationships_delete',
                    },
                    'GET': {
                        'function': 'relationships_get',
                    },
                    'PATCH': {
                        'function': 'relationships_patch',
                    },
                    'POST': {
                        'function': 'relationships_post',
                    },
                },
            },
        }

    def make_route_name(self, name, suffix=''):
        '''Attach prefix and suffix to name to generate a route_name.

        Arguments:
            name: A pyramid route name.

        Keyword Arguments:
            suffix: An (optional) suffix to append to the route name.
        '''
        return self.route_name_sep.join((self.route_name_prefix, name, suffix)).rstrip(self.route_name_sep)

    def make_route_pattern(self, name, suffix=''):
        '''Attach prefix and suffix to name to generate a route_name.

        Arguments:
            name: A pyramid route name.

        Keyword Arguments:
            suffix: An (optional) suffix to append to the route name.
        '''
        return self.route_pattern_sep.join((self.route_pattern_prefix, name, suffix)).rstrip(self.route_pattern_sep)

    def add_routes_views(self, view):
        '''Generate routes and views from the endpoints data object.

        Arguments:
            view: A view_class to associate routes and views with.
        '''

        for endpoint, endpoint_opts in self.endpoints.items():
            route_name = self.make_route_name(view.collection_name, suffix=endpoint)
            route_pattern = self.make_route_pattern(view.collection_name,
                                                    suffix=endpoint_opts.get('route_pattern_suffix', ''))
            self.config.add_route(route_name, route_pattern)
            for http_method, method_opts in endpoint_opts['http_methods'].items():
                self.config.add_view(view, attr=method_opts['function'],
                                     request_method=http_method, route_name=route_name,
                                     renderer=method_opts.get('renderer', 'json'))