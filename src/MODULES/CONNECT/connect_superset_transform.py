import json
from rally import files
import logging
import __pl_logging
from connect_md_reader import SONY_ONE

LICENSOR = "SPHE"

LANGUAGE_MAPPING = {
    'es': 'es-419',
    'la-en': 'en-US',
    'pt-br': 'pt-BR',
}

PLATFORM_MAPPING = {
    '12773': 'Br',
    'TBD': 'Las',
}
"""
The following platform id's still need to be implemented in the PLATFORM_MAPPING above ^.
Open question is what the country codes are for each platform.

platform_id	platform_name
11732	Amazon > Chile > SVOD > Features > Sony One LATAM
11733	Amazon > Chile > SVOD > Series > Sony One LATAM
11734	Amazon > Colombia > SVOD > Features > Sony One LATAM
11735	Amazon > Colombia > SVOD > Series > Sony One LATAM
11736	Amazon > Mexico > SVOD > Features > Sony One LATAM
11737	Amazon > Mexico > SVOD > Series > Sony One LATAM
11738	Amazon > Brazil > SVOD > Features > Sony One LATAM
11739	Amazon > Brazil > SVOD > Series > Sony One LATAM
12382	App > SouthernCone > SVOD > Features_Series > Sony One LATAM
12383	App > Brazil > SVOD > Features_Series > Sony One LATAM
12384	App > NorthernCone > SVOD > Features_Series > Sony One LATAM
12386	Affiliates > SouthernCone > SVOD > Features_Series > Sony One LATAM
12387	Affiliates > Brazil > SVOD > Features_Series > Sony One LATAM
12388	Affiliates > NorthernCone > SVOD > Features_Series > Sony One LATAM
12745	App > SouthernCone > FVOD > Features_Series > Sony One LATAM
12746	App > Brazil > FVOD > Features_Series > Sony One LATAM
12747	App > Andean > SVOD > Features_Series > Sony One LATAM
12748	App > Andean > FVOD > Features_Series > Sony One LATAM
12749	App > NorthernCone > FVOD > Features_Series > Sony One LATAM
12750	Affiliates > SouthernCone > FVOD > Features_Series > Sony One LATAM
12751	Affiliates > Brazil > FVOD > Features_Series > Sony One LATAM
12752	Affiliates > Andean > SVOD > Features_Series > Sony One LATAM
12753	Affiliates > Andean > FVOD > Features_Series > Sony One LATAM
12754	Affiliates > NorthernCone > FVOD > Features_Series > Sony One LATAM
12755	Amazon > Brazil > FVOD > Series > Sony One LATAM
12756	Amazon > Colombia > FVOD > Series > Sony One LATAM
12757	Amazon > Chile > FVOD > Series > Sony One LATAM
12758	Amazon > Mexico > FVOD > Series > Sony One LATAM
12759	Amazon > Brazil > FVOD > Features > Sony One LATAM
12760	Amazon > Colombia > FVOD > Features > Sony One LATAM
12761	Amazon > Chile > FVOD > Features > Sony One LATAM
12762	Amazon > Mexico > FVOD > Features > Sony One LATAM
"""


RATING_SYSTEM_MAPPING = {
    'mexico_rating_system': 'MX',
    'mpaa_rating_system': 'US',
    'incaa_rating_system': 'AR',
    'tv_rating_system': 'US',
    'rating_system': 'BR',
}

class ConnectSupersetTransformException(Exception):
    """ """


class Inventory:
    def __init__(self, superset):
        self.superset = superset
        self.video = self.get_video()
        self.audio = self.get_audio()

    def get_video(self):
        return []

    def get_audio(self):
        return []

    def build_json(self):
        return {
            'Video': self.video or None,
            'Audio': self.audio or None,
        }

class Presentations:
    def __init__(self, superset):
        self.superset = superset
        self.id = self.get_id()
        self.tracks = self.get_tracks()

    def get_id(self):
        return ''

    def get_tracks(self):
        return []

    def build_json(self):
        return {
            'ID': self.id or None,
            'Tracks': self.tracks or None,
        }

class CoreMetadata:
    def __init__(self, superset, language, md_type):
        self.superset = superset
        self.language = language
        self.md_type = md_type
        self.id = self.get_id()
        self.localized_info = self.get_localized_info()
        self.release_year = self.get_release_year()
        self.release_date = self.get_release_date()
        self.work_type = self.get_work_type()
        self.alt_identifier = self.get_alt_identifier()
        self.people = self.get_people()
        self.country_of_origin = self.get_country_of_origin()
        self.original_language =  self.get_original_language()
        self.associated_org = self.get_associated_org()
        self.company_display_credit = self.get_company_display_credit()

    @staticmethod
    def clean_list_of_strings(some_list):
        list_without_dupes = list(set(some_list))  # deduplicate the list
        final_list = [item for item in list_without_dupes if item]  # remove empty strings
        return final_list

    def get_id(self):
        if self.md_type == 'Episode':
            platform_id = self.superset.platform_details.id
            eidr_string = f"eidr_id_{PLATFORM_MAPPING[platform_id].lower()}"
            eidr_id = getattr(self.superset.title_details.metadata.items[SONY_ONE], eidr_string)
        elif self.md_type == 'Season':
            eidr_id = self.superset.title_group_details.metadata.items[SONY_ONE].eidr_id
        elif self.md_type == 'Series':
            eidr_id = self.superset.brand_details.metadata.items[SONY_ONE].eidr_id
        else:
            raise Exception(f"Unexpected md_type {self.md_type}")
        return f"md:cid:eidr-x:{eidr_id}:{LICENSOR}:metadata.feature"

    def get_localized_info(self):
        md_type_to_items_mapping = {
            'Episode': self.superset.title_details.metadata.items,
            'Season': self.superset.title_group_details.metadata.items,
            'Series': self.superset.brand_details.metadata.items,
        }
        items = md_type_to_items_mapping[self.md_type]
        language = self.language

        if self.md_type == 'Series':
            summaries = [
                items[language].synopsis,
                items[language].medium_synopsis,
                items[language].long_synopsis
            ]
        else:
            summaries = [
                items[language].short_description,
                items[language].medium_description,
                items[language].long_description,
            ]

        localized_info = [
            {
                'Language': LANGUAGE_MAPPING[language],
                'TitleDisplays': CoreMetadata.clean_list_of_strings([items[language].display_name]),
                'Summaries': CoreMetadata.clean_list_of_strings(summaries),
                'Genres': CoreMetadata.clean_list_of_strings(items[language].genres),
                'CopyrightLine': self.superset.general_details.copyright_owners,
            }
        ]
        return localized_info

    def get_release_year(self):
        return self.superset.general_details.release_year

    def get_release_date(self):
        return self.superset.general_details.release_date

    def get_work_type(self):
        return self.md_type

    def get_alt_identifier(self):
        platform_id = self.superset.platform_details.id
        eidr_string = f"eidr_id_{PLATFORM_MAPPING[platform_id].lower()}"
        eidr_attr = getattr(self.superset.title_details.metadata.items[SONY_ONE], eidr_string)
        return {
            'namespace': 'EIDR',
            'Identifier': eidr_attr,
        }

    def get_people(self):
        people = []
        md_type_to_items_mapping = {
            'Episode': self.superset.title_details.metadata.items,
            'Season': self.superset.title_group_details.metadata.items,
            'Series': self.superset.brand_details.metadata.items,
        }
        items = md_type_to_items_mapping[self.md_type]

        actors = items[self.language].actors or []
        for actor in actors:
            item = {
                'Job': {
                    'JobFunction': 'Actor'
                },
                'Name': {
                    'DisplayName': actor,
                    'Language': LANGUAGE_MAPPING[self.language]
                }
            }
            people.append(item)

        directors = items[self.language].directors or []
        for director in directors:
            item = {
                'Job': {
                    'JobFunction': 'Directors'
                },
                'Name': {
                    'DisplayName': director,
                    'Language': LANGUAGE_MAPPING[self.language]
                }
            }
            people.append(item)

        writers = items[self.language].writers or []
        for writer in writers:
            item = {
                'Job': {
                    'JobFunction': 'Writer'
                },
                'Name': {
                    'DisplayName': writer,
                    'Language': LANGUAGE_MAPPING[self.language]
                }
            }
            people.append(item)

        producers = items[self.language].producers or []
        for producer in producers:
            item = {
                'Job': {
                    'JobFunction': 'Producer'
                },
                'Name': {
                    'DisplayName': producer,
                    'Language': LANGUAGE_MAPPING[self.language]
                }
            }
            people.append(item)

        return people

    def get_country_of_origin(self):
        md_type_to_items_mapping = {
            'Episode': self.superset.title_details.metadata.items,
            'Season': self.superset.title_group_details.metadata.items,
            'Series': self.superset.brand_details.metadata.items,
        }
        return md_type_to_items_mapping[self.md_type]['la-en'].source_origins

    def get_original_language(self):
        if self.md_type == 'Episode':
            return self.superset.title_details.metadata.items['la-en'].original_language
        elif self.md_type == 'Season':
            return self.superset.title_group_details.metadata.items[SONY_ONE].original_language
        elif self.md_type == 'Series':
            return self.superset.brand_details.metadata.items['la-en'].original_language
        else:
            raise Exception(f"Unexpected md_type {self.md_type}")

    def get_associated_org(self):
        return {"display_name": f"{LICENSOR}"}

    def get_company_display_credit(self):
        return CoreMetadata.clean_list_of_strings(self.superset.general_details.studios)

    def build_json(self):
        return {
            'Basic': {
                'ID': self.id or None,
                'LocalizedInfo': self.localized_info or None,  # One language only
                'ReleaseYear': self.release_year or None,
                'ReleaseDate': self.release_date or None,
                'WorkType': self.work_type or None,
                'AltIdentifier': self.alt_identifier or None,
                'People': self.people or None,
                'CountryOfOrigin': self.country_of_origin or None,
                'OriginalLanguage': self.original_language or None,
                'AssociatedOrg': self.associated_org or None,
            },
            'CompanyDisplayCredit': self.company_display_credit or None,
        }


class EpisodeCoreMetadata(CoreMetadata):
    def __init__(self, superset, language):
        super().__init__(superset, language, 'Episode')
        self.rating_set = self.get_rating_set()
        self.sequence_info = self.get_sequence_info()

    def get_sequence_info(self):
        return self.superset.title_details.episode_number

    def get_rating_values_from_title_details(self, rating_system, rating):
        items = self.superset.title_details.metadata.items[self.language]
        if getattr(items, rating_system) and getattr(items, rating):
            return getattr(items, rating_system), getattr(items, rating)
        raise Exception(f"Cannot find rating for '{rating_system}'/'{rating}'")

    def get_rating_values(self, rating_system, rating):
        items = self.superset.asset_details.metadata.items[self.language]
        if getattr(items, rating_system) and getattr(items, rating_system):
            return getattr(items, rating_system), getattr(items, rating_system)
        else:
            rating_system_value, rating_value = self.get_rating_values_from_title_details(rating_system, rating)
            return rating_system_value, rating_value

    def get_rating_dict(self, rating_system, rating_system_value, rating_value):
        rating_dict = {
            'Region': {
                'Country': RATING_SYSTEM_MAPPING[rating_system]
            },
            'System': rating_system_value,
            'Value': rating_value
        }
        return rating_dict

    def get_rating_set(self):
        res = []
        if self.language == 'es':
            rating_system = 'mexico_rating_system'
            rating = 'mexico_rating'
            rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            res.append(rating_dict)

            # Next rating is commented out because content is episodic, not motion picture
            # rating_system = 'mpaa_rating_system'
            # rating = 'mpaa_rating'
            # rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            # rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            # res.append(rating_dict)

            rating_system = 'incaa_rating_system'
            rating = 'incaa_rating'
            rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            res.append(rating_dict)
        elif self.language == 'la-en':
            rating_system = 'tv_rating_system'
            rating = 'tv_rating'
            rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            res.append(rating_dict)

            # Next rating is commented out because content is episodic, not motion picture
            # rating_system = 'mpaa_rating_system'
            # rating = 'mpaa_rating'
            # rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            # rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            # res.append(rating_dict)
        elif self.language == 'pt-br':
            rating_system = 'rating_system'
            rating = 'rating'
            rating_system_value, rating_value = self.get_rating_values(rating_system, rating)
            rating_dict = self.get_rating_dict(rating_system, rating_system_value, rating_value)
            res.append(rating_dict)
        return res

    def build_json(self):
        res = super().build_json()
        res['Basic']['SequenceInfo'] = self.sequence_info or None
        res['Basic']['RatingSet'] = self.rating_set or None
        return res


class SeasonCoreMetadata(CoreMetadata):
    def __init__(self, superset, language):
        super().__init__(superset, language, 'Season')
        self.sequence_info = self.get_sequence_info()

    def get_sequence_info(self):
        return self.superset.title_group_details.season_number

    def build_json(self):
        res = super().build_json()
        res['Basic']['SequenceInfo'] = self.sequence_info or None
        return res


class SeriesCoreMetadata(CoreMetadata):
    def __init__(self, superset, language):
        super().__init__(superset, language, 'Series')
        # No rating_set in the Amazon examples at series level, even though present in the source

    def build_json(self):
        return super().build_json()


class ConnectSupersetTransform:
    logger = logging.getLogger(__qualname__)

    def __init__(self, superset):
        self.superset = superset

    def get_id(self):
        return "manifest id here"

    def get_compatibility(self):
        return {'spec_version': '1.12', 'profile': 'MMC-1'}

    def get_languages(self, md_type):
        md_type_to_items_mapping = {
            'Episode': self.superset.title_details.metadata.items,
            'Season': self.superset.title_group_details.metadata.items,
            'Series': self.superset.brand_details.metadata.items,
        }
        languages = list(md_type_to_items_mapping[md_type].keys())
        languages.remove(SONY_ONE)
        return languages

    def build_json(self):
        res = {
            'manifest': self.get_id() or None,
            'compatibility': self.get_compatibility() or None,
            'inventory': Inventory(self.superset).build_json(),
            'presentations': Presentations(self.superset).build_json(),
            'entertainment_core': []  # Populated at the end of this method
        }

        languages = self.get_languages('Episode')
        episode_core = {
            'type': 'episode',
            'core_metadatas': []
        }
        for language in languages:
            episode_core['core_metadatas'].append({'core_metadata': EpisodeCoreMetadata(self.superset, language).build_json()})

        languages = self.get_languages('Season')
        season_core =  {
            'type': 'season',
            'core_metadatas': []
        }
        for language in languages:
            season_core['core_metadatas'].append({'core_metadata': SeasonCoreMetadata(self.superset, language).build_json()})

        languages = self.get_languages('Series')
        series_core =  {
            'type': 'series',
            'core_metadatas': []
        }
        for language in languages:
            series_core['core_metadatas'].append({'core_metadata': SeriesCoreMetadata(self.superset, language).build_json()})

        res['entertainment_core'] = [episode_core, season_core, series_core]
        return res

    def transform(self, file_uri, label, tags=None):
        res = self.build_json()
        self.save_file(file_uri, label, json.dumps(res, indent=4), tags)

    def save_file(self, file_uri, label, output, tags=None):
        self.logger.info(f"Transformed metadata: {output}")
        files.write_file(file_uri, output.encode())
        files.add_inventory(file_uri, label, tags=tags or [])
        self.logger.info(f"Metadata transformation saved to inventory")

