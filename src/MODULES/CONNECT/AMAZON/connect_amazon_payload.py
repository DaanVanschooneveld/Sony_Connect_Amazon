class Payload:
    def __init__(self, data):
        self.endpoint = data.get("endpoint", "amazon")
        self.output_filenames = data.get("output_filenames", {})
        self.publication_type = data.get("publication_type", "first delivery")
        self.metadata_label = data.get("metadata_label", f"connect_{self.endpoint}_metadata")

    def to_json(self):
        return {
            "endpoint": self.endpoint,
            "output_filenames": self.output_filenames,
            "publication_type": self.publication_type,
            "metadata_label": self.metadata_label
        }
