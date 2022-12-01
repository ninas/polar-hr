class EquipmentParsingMixin():
    def _extract_bands(self, val):
        bands = []
        for i in filter(None, val.split(",")):
            bands.append(
                {"quantity": 1, "magnitude": i.strip()}
            )
        return bands

    def _extract_weights(self, val):
        equipment = []
        for i in filter(None, val.split(",")):
            dd = {"quantity": 2}
            i = i.strip()

            if i.startswith("one"):
                dd["quantity"] = 1
                i = i[3:].strip()

            dd["magnitude"] = i.strip()
            equipment.append(dd)
        return equipment
