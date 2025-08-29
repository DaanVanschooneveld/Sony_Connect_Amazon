from __pl_files import RallyFiles
import jmespath

SONY_ONE = 'so'

def extract_value(path, data_set):
    """
    Extracts and returns value of key pointed to by path in data set.  Supports strings and lists.  Examples:

    data_set = {"scheduling-type": "archive"}
    path = '"scheduling-type"'
    -> returns 'archive'

    data_set = {"id":{"@type":"integer","#text":"21857943"}}
    path = 'id."#text"'
    -> returns '21857943'

    data_set = {"id":{"@type":"integer","#text":"21857943"}}
    path = 'id'
    -> also returns '21857943'

    data_set = {"so-la-en-brand-studios":{"@type":"array","so-la-en-brand-studio":"TF1"}}
    path = '"so-la-en-brand-studios"'
    -> returns 'TF1'

    data_set = {"so-la-en-brand-genres":{"@type":"array","so-la-en-brand-genre":["Action - Crime","Comedy"]}}
    path = '"so-la-en-brand-genres"'
    -> returns ['Action - Crime','Comedy']
    """
    struct = jmespath.search(path, data_set)
    if isinstance(struct, str):
        return struct
    elif isinstance(struct, dict):
        keys = list(struct.keys())
        keys.remove('@type')
        if len(keys) == 1:
            expression = '"' + keys[0] + '"'
            return jmespath.search(expression, struct)
        elif len(keys) > 1:
            raise Exception(f"Too many nested levels in struct: {struct}")

def remove_special_chars(s):
    special_chars = [">", "<", ":", "|", "?", "*"]
    for char in special_chars:
        s = s.replace(char, "")
    return s

class NoMatchingKeyException(Exception):
    """ """


class GeneralDetails:
    def __init__(self, document_data):
        self.id = extract_value('id', document_data) or ""
        self.external_id = extract_value('external_id', document_data) or ""
        self.put_up = extract_value('"put-up"', document_data) or ""
        self.take_down = extract_value('"take-down"', document_data) or ""
        self.scheduling_type = extract_value('"scheduling-type"', document_data) or ""
        self.copyright_owners = ""
        self.release_year = ""
        self.release_date = ""
        self.studios = ""

    def __getitem__(self, name):
        return getattr(self, name)

    def __repr__(self):
        return (f"--> General Details:\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Put Up: {self.put_up or 'None'}\n"
                f"\t- Take Down: {self.take_down or 'None'}\n"
                f"\t- Scheduling Type: {self.scheduling_type or 'None'}\n"
                f"\t- Copyright Owners: {self.copyright_owners or 'None'}\n"
                f"\t- Release Year: {self.release_year or 'None'}\n"
                f"\t- Release Date: {self.release_date or 'None'}\n"
                f"\t- Studios: {self.studios or 'None'}\n"
                )


class PlatformDetails:
    def __init__(self, platform_data):
        self.name = extract_value('name', platform_data)
        self.id = extract_value('id', platform_data) or extract_value('id', platform_data)
        self.external_id = extract_value('"external-id"', platform_data)

    def __repr__(self):
        return (f"--> Platform Details:\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Name: {self.name or 'None'}\n"
                )


class MetadataItem:
    def create_attributes(self, prefix, localized_data, separator):
        keys = list(localized_data.keys())
        keys_for_lang = [key for key in keys if key.startswith(f"{prefix}-{separator}-")]
        attr_names_for_lang = [key.replace(f"{prefix}-{separator}-", "", 1).replace('-', '_') for key in keys_for_lang]
        for attr, key in zip(attr_names_for_lang, keys_for_lang):
            expression = '"' + key + '"'
            value = extract_value(expression, localized_data)
            if attr in ['genres', 'actors', 'writers', 'directors', 'producers', 'studios'] and isinstance(value, str):
                value = [value]
            setattr(self, attr, value)

    def __repr__(self):
        repr_string = ""
        attrs_dict = vars(self)
        for attr_name in attrs_dict:
            string_to_add = f"\t\t\t- {attr_name.replace('_', ' ').title()}: {attrs_dict[attr_name]}\n"
            repr_string += string_to_add
        return repr_string


class Metadata:
    def __init__(self, items=None):
        self.items = items

    @staticmethod
    def extract_prefixes(metadata, separator):
        prefixes = []
        keys_without_separator = []
        for key in metadata:
            try:
                prefix = key[:key.index(f'-{separator}')]
            except ValueError:
                keys_without_separator.append(key)
            else:
                prefixes.append(prefix)
        prefixes = list(set(prefixes))
        keys_without_separator = list(set(keys_without_separator))
        prefixes.sort()  # SONY_ONE value, 'so', if present, will be first in the list after sorting
        keys_without_separator.sort()
        # print(f"prefixes: {prefixes}")
        # if keys_without_separator:
        #     print(f"Keys without separator '{separator}': {keys_without_separator}")
        return prefixes

    @classmethod
    def from_data_set(cls, data_set, separator):
        items = {}
        metadata = jmespath.search("metadata", data_set)
        del metadata['@type']
        prefixes = Metadata.extract_prefixes(metadata, separator)
        for prefix in prefixes:
            metadata_item = MetadataItem()
            metadata_item.create_attributes(prefix, metadata, separator)
            if prefix != SONY_ONE:
                language = prefix[(len(SONY_ONE) + 1):]
                items[language] = metadata_item
            else:
                items[SONY_ONE] = metadata_item
        return cls(items)

    def __repr__(self):
        repr_string = "\n"
        for key, value in self.items.items():
            repr_string += f"\t\t- {key}\n"
            repr_string += f"{value}"
        return repr_string


class BrandDetails:
    def __init__(self, brand_data):
        self.id = extract_value('id', brand_data) or ""
        self.external_id = extract_value('"external-id"', brand_data) or ""
        self.name = extract_value('name', brand_data) or ""
        self.name_no_special_chars = remove_special_chars(self.name)
        self.licensor = extract_value('licensor.name', brand_data) or ""
        self.metadata = Metadata.from_data_set(brand_data, 'brand')
        self.images = []
        self.contributors = []
        self.clips = []

    def __repr__(self):
        return (f"--> Brand Details (Series):\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Name: {self.name or 'None'}\n"
                f"\t- Name without special chars: {self.name_no_special_chars or 'None'}\n"
                f"\t- Licensor: {self.licensor or 'None'}\n"
                f"\t- Metadata:{self.metadata or 'None'}\n"
                f"\t- Images: {', '.join([str(x) for x in self.images]) or 'None'}\n"
                f"\t- Contributors: {', '.join([str(x) for x in self.contributors]) or 'None'}\n"
                f"\t- Clips: {self.clips or 'None'}\n"
                )


class TitleGroupDetails:
    def __init__(self, title_group_data):
        self.id = extract_value('id', title_group_data) or ""
        self.external_id = extract_value('"external-id"', title_group_data) or ""
        self.name = extract_value('name', title_group_data) or ""
        self.title_group_type = extract_value('"title-group-type"', title_group_data) or ""
        self.season_number = extract_value('"season-number"', title_group_data) or ""
        self.season_reference_id = extract_value('"season-reference-id"', title_group_data) or ""
        self.metadata = Metadata.from_data_set(title_group_data, 'group')
        self.images = []
        self.contributors = []
        self.clips = []

    def __repr__(self):
        return (f"--> Title Group Details (Season):\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Name: {self.name or 'None'}\n"
                f"\t- Title Group Type: {self.title_group_type or 'None'}\n"
                f"\t- Season Number: {self.season_number or 'None'}\n"
                f"\t- Season Reference ID: {self.season_reference_id or 'None'}\n"
                f"\t- Metadata: {self.metadata or 'None'}\n"
                f"\t- Images: {', '.join([str(x) for x in self.images]) or 'None'}\n"
                f"\t- Contributors: {', '.join([str(x) for x in self.contributors]) or 'None'}\n"
                f"\t- Clips: {self.clips or 'None'}\n"
                )


class TitleDetails:
    def __init__(self, title_data):
        self.id = extract_value('id', title_data) or ""
        self.external_id = extract_value('"external-id"', title_data) or ""
        self.name = extract_value('name', title_data) or ""
        self.episode_number = extract_value('"episode-number"', title_data) or ""
        self.episode_reference_id = extract_value('"episode-reference-id"', title_data) or ""
        self.title_type = extract_value('"title-type"', title_data) or ""
        self.licensor = extract_value('licensor.name', title_data) or ""
        self.metadata = Metadata.from_data_set(title_data, 'title')
        self.copyright_owners = extract_value('metadata."so-la-en-copyright-owners"', title_data) or ""
        self.episode_position = extract_value('"ad-hoc-metadata"."episode-position"', title_data) or ""
        self.images = []
        self.contributors = []
        self.clips = []

    def __repr__(self):
        return (f"--> Title Details (Episode):\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Name: {self.name or 'None'}\n"
                f"\t- Episode Number: {self.episode_number or 'None'}\n"
                f"\t- Episode Reference ID: {self.episode_reference_id or 'None'}\n"
                f"\t- Title Type: {self.title_type or 'None'}\n"
                f"\t- Licensor: {self.licensor or 'None'}\n"
                f"\t- Metadata: {self.metadata or 'None'}\n"
                f"\t- Copyright Owners: {self.copyright_owners or 'None'}\n"
                f"\t- Episode Position: {self.episode_position or 'None'}\n"
                f"\t- Images: {', '.join([str(x) for x in self.images]) or 'None'}\n"
                f"\t- Contributors: {', '.join([str(x) for x in self.contributors]) or 'None'}\n"
                f"\t- Clips: {self.clips or 'None'}\n"
                )


class AssetDetails:
    def __init__(self, asset_data):
        self.id = extract_value(f'id', asset_data) or ""
        self.external_id = extract_value(f'"external-id"', asset_data) or ""
        self.type = extract_value(f'type', asset_data) or ""
        self.name = extract_value(f'name', asset_data) or ""
        self.description = extract_value(f'description', asset_data) or ""
        self.runtime = extract_value(f'runtime', asset_data) or ""
        self.metadata = Metadata.from_data_set(asset_data, 'title')
        self.runtime_in_frames = extract_value(f'"ad-hoc-metadata"."runtime-in-frames"', asset_data) or ""
        self.runtime_in_frames_segments = extract_value(f'"ad-hoc-metadata"."runtime-in-frames-segments"', asset_data) or []
        self.renditions = extract_value(f'renditions', asset_data) or []
        self.segments = extract_value(f'segments', asset_data) or []

    def __repr__(self):
        return (f"--> Asset Details:\n"
                f"\t- ID: {self.id or 'None'}\n"
                f"\t- External ID: {self.external_id or 'None'}\n"
                f"\t- Type: {self.type or 'None'}\n"
                f"\t- Name: {self.name or 'None'}\n"
                f"\t- Description: {self.description or 'None'}\n"
                f"\t- Runtime: {self.runtime or 'None'}\n"
                f"\t- Metadata: {self.metadata or 'None'}\n"
                f"\t- runtime In Frames: {self.runtime_in_frames or 'None'}\n"
                f"\t- Runtime In Frames Segments: {self.runtime_in_frames_segments or 'None'}\n"
                f"\t- Renditions: {self.renditions or 'None'}\n"
                f"\t- Segments: {self.segments or 'None'}\n"
                )


class SuperSet:
    rallyfiles = RallyFiles()

    def __init__(self, xml_content_dict):
        self.xml_content_dict = xml_content_dict
        self.general_details = GeneralDetails(jmespath.search('scheduling', self.xml_content_dict))
        self.platform_details = PlatformDetails(jmespath.search('scheduling.platform', self.xml_content_dict))
        self.brand_details = BrandDetails(jmespath.search('scheduling.brand', self.xml_content_dict))
        self.title_group_details = TitleGroupDetails(jmespath.search('scheduling."title-group"', self.xml_content_dict))
        self.title_details = TitleDetails(jmespath.search('scheduling.title', self.xml_content_dict))
        self.asset_details = AssetDetails(jmespath.search('scheduling.asset', self.xml_content_dict))
        self.copy_to_general_details()

    def copy_to_general_details(self):
        self.general_details.copyright_owners = self.title_details.copyright_owners
        self.general_details.release_year = self.title_details.metadata.items[SONY_ONE].release_year
        self.general_details.release_date = self.title_details.metadata.items[SONY_ONE].original_release_air_date
        self.general_details.studios = self.title_details.metadata.items['la-en'].studios

    def __repr__(self):
        return (f"SuperSet:\n\n"
                f"{self.general_details}\n"
                f"{self.platform_details}\n"
                f"{self.brand_details}\n"
                f"{self.title_group_details}\n"
                f"{self.title_details}\n"
                f"{self.asset_details}\n"
                )

    @classmethod
    def from_file_uri(cls, file_uri):
        content_dict = SuperSet.rallyfiles.extract_xml_from_fileuri(file_uri)
        return cls(content_dict)

    @classmethod
    def from_label(cls, label):
        content_dict = SuperSet.rallyfiles.get_xml_content_as_dict(label)
        return cls(content_dict)
