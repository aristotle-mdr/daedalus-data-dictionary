from aristotle_mdr.apps import AristotleExtensionBaseConfig

class DaedalusStorageConfig(AristotleExtensionBaseConfig):
    name = 'daedalus_data_dictionary.storage'
    verbose_name = "Daedalus Data Dictionary Extension"
    description = "Daedalus Data Dictionary adds a new content types for building and importing data dictionaries."
