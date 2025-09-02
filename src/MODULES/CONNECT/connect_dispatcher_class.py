import logging
import __pl_logging
from __pl_files import RallyFiles
from rally import supplyChain
from rally_connect import (deliver, takedown, update, metadata_update, redeliver)
from rally_connect import (MediaFile, CaptionFile, ImageFile, MetadataFile)

STEP_NAME = "connect_dispatcher"
logger = logging.getLogger(STEP_NAME)


class MissingFileException(Exception):
    """ """

class ConnectDispatch:
    EVENT_CALLBACK_SUPPLY_CHAIN_STEP = "connect_010_event_handler"

    def __init__(self,
                 endpoint,
                 package_id=None):
        self.rf = RallyFiles()
        self.endpoint = endpoint
        self.media_list = []
        self.metadata = None
        self.captions = []
        self.audio_list = []
        self.images = []
        self.event_callback = supplyChain.SupplyChainStep(ConnectDispatch.EVENT_CALLBACK_SUPPLY_CHAIN_STEP)
        self.config_url = None
        self.wip_storage_url = None
        self.delivery_url_override = None
        self.delivery_credentials_override = None
        self.version = "0.35.0"
        self.trim_media = None
        self.client_data = None
        self.package_id = package_id or None

        self.endpoint_name_override = None

    @classmethod
    def create_from_action(cls,
                           endpoint,
                           publication_type,
                           package_id=None):
        action_class_mapping = {
            "deliver":          ConnectDispatchDeliver,
            "redeliver":        ConnectDispatchRedeliver,
            "update":           ConnectDispatchUpdate,
            "metadata update":  ConnectDispatchMetadataUpdate,
            "takedown":         ConnectDispatchTakedown
        }
        action = {
            "first delivery": "deliver",
            "initial delivery": "deliver",
            "full package replacement": "redeliver",
            "redelivery": "redeliver",
            "metadata update": "metadata update",
            "metadata update (mdu)": "metadata update"
        }
        logger.info(f"Publication Type: {publication_type}")
        if publication_type.lower() not in action:
            raise ValueError(f"Connect Action: [{publication_type}] not supported")
        return action_class_mapping[action[publication_type.lower()]](endpoint,
                                                                      package_id=package_id)

    def add_media(self, label,
                  scopes,
                  purposes,
                  language = None,
                  text = None,
                  audio = None):
        if not self.rf.is_label_available(label):
            raise MissingFileException(f"Media file with label {label} not found")
        new_media = MediaFile(label=label,
                              audio=audio,
                              scopes=scopes,
                              purposes=purposes,
                              text=text)
        self.media_list.append(new_media)

    def set_metadata(self, label, language=None):
        self.metadata = MetadataFile(label=label, language=language)

    def add_captions(self, label,
                     scopes,
                     purposes,
                     language = None):
        """Placeholder: Adds one or more caption files."""
        new_media = CaptionFile(label=label,
                                language=language,
                                scopes=scopes,
                                purposes=purposes)
        self.captions.append(new_media)

    def add_audio(self, name):
        """Placeholder: Adds one or more caption files."""
        pass

    def add_image(self, label,
                  scopes,
                  purposes,
                  language = None,
                  text = None):
        new_image = ImageFile(label=label,
                              scopes=scopes,
                              purposes=purposes)
        self.images.append(new_image)

    def process_connect(self):
        return None


""" DELIVER """
class ConnectDispatchDeliver(ConnectDispatch):
    def process_connect(self):
        return deliver(endpoint=self.endpoint_name_override or self.endpoint.lower(),
                       media=self.media_list,
                       metadata=self.metadata,
                       captions=self.captions,
                       audio=self.audio_list,
                       image=self.images,
                       event_callback=self.event_callback,
                       config_url=self.config_url,
                       wip_storage_url=self.wip_storage_url,
                       delivery_url_override=self.delivery_url_override,
                       delivery_credentials_override=self.delivery_credentials_override,
                       version=self.version,
                       trim_media=self.trim_media,
                       package_id=self.package_id,
                       client_data={"endpoint": self.endpoint.lower()})



class ConnectDispatchRedeliver(ConnectDispatchDeliver):
    def process_connect(self):
        return redeliver(endpoint=self.endpoint_name_override or self.endpoint.lower(),
                         media=self.media_list,
                         metadata=self.metadata,
                         captions=self.captions,
                         audio=self.audio_list,
                         image=self.images,
                         event_callback=self.event_callback,
                         config_url=self.config_url,
                         wip_storage_url=self.wip_storage_url,
                         delivery_url_override=self.delivery_url_override,
                         delivery_credentials_override=self.delivery_credentials_override,
                         version=self.version,
                         trim_media=self.trim_media,
                         package_id=self.package_id,
                         client_data={"endpoint": self.endpoint.lower()})


""" UPDATES """
class ConnectDispatchUpdate(ConnectDispatch):
    def process_connect(self):
        return update(endpoint=self.endpoint_name_override or self.endpoint.lower(),
                      media=self.media_list,
                      metadata=self.metadata,
                      captions=self.captions,
                      audio=self.audio_list,
                      image=self.images,
                      event_callback=self.event_callback,
                      config_url=self.config_url,
                      wip_storage_url=self.wip_storage_url,
                      delivery_url_override=self.delivery_url_override,
                      delivery_credentials_override=self.delivery_credentials_override,
                      version=self.version,
                      trim_media=self.trim_media,
                      package_id=self.package_id,
                      client_data={"endpoint": self.endpoint.lower()})


class ConnectDispatchMetadataUpdate(ConnectDispatchUpdate):
    def process_connect(self):
        return metadata_update(endpoint=self.endpoint_name_override or self.endpoint.lower(),
                               metadata=self.metadata,
                               event_callback=self.event_callback,
                               config_url=self.config_url,
                               wip_storage_url=self.wip_storage_url,
                               delivery_url_override=self.delivery_url_override,
                               delivery_credentials_override=self.delivery_credentials_override,
                               version=self.version,
                               trim_media=self.trim_media,
                               package_id=self.package_id,
                               client_data={"endpoint": self.endpoint.lower()})


""" takedown/expire """
class ConnectDispatchTakedown(ConnectDispatch):
    def process_connect(self):
        return takedown(endpoint=self.endpoint_name_override or self.endpoint.lower(),
                        metadata=self.metadata,
                        event_callback=self.event_callback,
                        config_url=self.config_url,
                        delivery_url_override=self.delivery_url_override,
                        delivery_credentials_override=self.delivery_credentials_override,
                        version=self.version,
                        package_id=self.package_id,
                        client_data={"endpoint": self.endpoint.lower()})