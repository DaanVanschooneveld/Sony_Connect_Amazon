from rally import supplyChain, asset
import logging
import __pl_logging
from __pl_status_transitions import StatusHelper
from connect_amazon_transitions import STATUS_TRANSITIONS
from connect_amazon_payload import Payload
from connect_md_reader import SuperSet
from connect_amazon_superset_transform import AmazonConnectSupersetTransform

STEP_NAME = "delivery"
logger = logging.getLogger(STEP_NAME)
status_helper = StatusHelper(STATUS_TRANSITIONS, STEP_NAME)

LABEL = "Bebanjo output"

def prepare_metadata(payload: Payload):
    user_md = asset.get_user_metadata() or {}
    connect_deliveries = user_md.get("connect_deliveries") or {}
    connect_deliveries[payload.endpoint] = payload.to_json()

    asset.update_user_metadata({"connect_deliveries": connect_deliveries})


def eval_main(context):
    data = context.get('dynamicPresetData') or {}
    payload = Payload(data)
    logger.info(f"payload: {payload}\n----\n")

    prepare_metadata(payload)

    asset_name = asset.get_asset()["name"]

    status_helper.execute_transition("on_start", parameters_dict={"endpoint": payload.endpoint.lower()})

    superset = SuperSet.from_label(LABEL)
    logger.info(f"{superset}")

    md_connect = AmazonConnectSupersetTransform(superset)

    metadata_label = f"connect_{payload.endpoint.lower()}_metadata"
    md_connect.transform(f"rsl://js-store/DVS/Sony/Sources/{asset_name}/{asset_name}_{payload.endpoint}_metadata.json",
                         metadata_label,
                         [f"{payload.endpoint.lower()}"])

    data["metadata_label"] = metadata_label
    # return True
    return supplyChain.start_new_supply_chain(asset.get_asset()["name"],
                                              "resume",
                                              dynamic_preset_data=data,
                                              client_resource_id=payload.endpoint.lower())
