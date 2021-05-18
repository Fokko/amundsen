import json
import logging
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Union

# TODO change all imports to use common dependecy instead
from amundsen_common.models.feature import FeatureSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.entity.resource_type import ResourceType
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client

LOGGER = logging.getLogger(__name__)


class FeatureDetailAPI(Resource):
    """
    FeatureDetail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            feature = self.client.get_feature(feature_uri=feature_uri)
            schema = FeatureSchema()
            return schema.dump(feature), HTTPStatus.OK
        except NotFoundException:
            return {'message': f'feature_uri {feature_uri} does not exist'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            return {'message': f'Internal server error: {e}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class FeatureLineageAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/lineage_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureStatsAPI(Resource):

    # TODO integrate stats source for FE
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureGenerationCodeAPI(Resource):

    # TODO use Query common model
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureSampleAPI(Resource):

    # TODO use DataSample common model
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/detail_get.yml')
    def get(self, feature_uri: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureOwnerAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/feature/owner_put.yml')
    def put(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        pass

    @swag_from('swagger_doc/feature/owner_delete.yml')
    def delete(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        pass


class FeatureDescriptionAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @swag_from('swagger_doc/common/description_get.yml')
    def get(self, id: str) -> Iterable[Any]:
        """
        Returns description in Neo4j endpoint
        """
        try:
            description = self.client._get_resource_description(resource_type=ResourceType.Feature,
                                                                uri=id).description
            return {'description': description}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'feature_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Any]:
        """
        Updates table description (passed as a request body)
        """
        try:
            description = json.loads(request.data).get('description')
            self.client._put_resource_description(resource_type=ResourceType.Feature,
                                                  uri=id, description=description)
            return None, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND


class FeatureTagAPI(Resource):
    """
    Only for user tags not owner tags
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, required=False, default='default')

        self._tag_common = TagCommon(client=self.client)

    @swag_from('swagger_doc/tag/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        # use tag_type to distinguish between tag and badge
        tag_type = args.get('tag_type', 'default')

        if tag_type == 'owner':
            return \
                {'message': f'The tag {tag} for id {id} with type {tag_type} '
                            f'and resource_type {ResourceType.Feature.name} is '
                            'not added successfully because owner tags are not editable'}, \
                        HTTPStatus.CONFLICT

        return self._tag_common.put(id=id,
                                    resource_type=ResourceType.Feature,
                                    tag=tag,
                                    tag_type=tag_type)

    @swag_from('swagger_doc/tag/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')
        if tag_type == 'owner':
            return \
                {'message': f'The tag {tag} for id {id} with type {tag_type} '
                            f'and resource_type {ResourceType.Feature.name} is '
                            'not deleted because owner tags are not editable'}, \
                        HTTPStatus.CONFLICT

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Feature,
                                       tag=tag,
                                       tag_type=tag_type)


class FeatureBadgeAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, required=True)

        self._badge_common = BadgeCommon(client=self.client)

    @swag_from('swagger_doc/badge/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.put(id=id,
                                      resource_type=ResourceType.Feature,
                                      badge_name=badge,
                                      category=category)

    @swag_from('swagger_doc/badge/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Feature,
                                         badge_name=badge,
                                         category=category)
