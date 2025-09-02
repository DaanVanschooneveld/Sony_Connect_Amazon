import logging
import __pl_logging
from __pl_status_transitions import StatusHelper
from connect_amazon_transitions import STATUS_TRANSITIONS
from connect_amazon_payload import Payload
from connect_dispatcher_class import ConnectDispatch
from rally_connect import SCOPES, PURPOSES, TEXT
from __pl_files import RallyFiles


STEP_NAME = "delivery"
logger = logging.getLogger(STEP_NAME)
status_helper = StatusHelper(STATUS_TRANSITIONS, STEP_NAME)
rf = RallyFiles()

def eval_main(context):
    data = context.get('dynamicPresetData') or {}
    payload = Payload(data)
    logger.info(f"payload: {payload}\n----\n")

    status_helper.execute_transition("on_start", parameters_dict={"endpoint": payload.endpoint})

    dispatcher = ConnectDispatch.create_from_action(payload.endpoint,
                                                    payload.publication_type,
                                                    package_id=f"{context.get('assetId')}-{payload.endpoint.lower()}")

    dispatcher.delivery_url_override = "rsl://js-store/DVS/Sony/export/Connect/Amazon/"

    dispatcher.set_metadata(payload.metadata_label,
                            language="en")

    # dispatcher.add_media(label="movie",
    #                      scopes=[SCOPES.EPISODE],
    #                      purposes=[PURPOSES.MEDIA.PROGRAM],
    #                      language="en",
    #                      text=TEXT.TEXTED,
    #                      audio=[
    #                          {'channel_layout': ['L', 'R'], 'language': 'en'}
    #                      ])

    # # For demo purpose: Normally, an scc would need to be created
    # if rf.is_label_available("del_opt6_scc"): #del_opt6_scc
    #     dispatcher.add_captions("del_opt6_scc",
    #                             scopes=[SCOPES.EPISODE],
    #                             purposes=[PURPOSES.CAPTIONS.CAPTIONS],
    #                             language="en")

    # if rf.is_label_available("amazon_image_Cover Art"):
    #     dispatcher.add_image("amazon_image_Cover Art",
    #                          scopes=[SCOPES.EPISODE],
    #                          purposes=[PURPOSES.IMAGE.COVER])

    dispatcher.endpoint_name_override = "does_not_exist"
    return dispatcher.process_connect()
