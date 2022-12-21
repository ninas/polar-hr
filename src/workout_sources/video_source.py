import math
import re
import copy
from functools import cache, cached_property

from overrides import override

from src.db.workout.source import Source
from src.workout_sources.source_consts import SourceConsts


class VideoSource(Source):
    @cached_property
    @override(check_signature=False)
    def tags(self):
        tags = self._gen_tags()
        return self._clean_tags(tags)

    def _gen_tags(self):
        tags = set()
        if self.duration is not None:
            tags.add(self._gen_tag_from_duration())

        if self.title is not None:
            tags.update(self._add_from_text(self.title))
        return tags

    def _gen_tag_from_duration(self):
        in_mins = self.duration.total_seconds() / 60
        start = int(in_mins / 10) * 10
        end = math.ceil(in_mins / 10) * 10
        if start == end:
            end += 10
        return f"{start}-{end}min"

    def _clean_tags(self, potential_tags):
        strip_words = sorted(
            list(copy.deepcopy(SourceConsts.strip_words)), key=len, reverse=True
        )
        tags = set()
        for i in sorted(potential_tags, key=len):
            i = i.lower().strip()

            if i in SourceConsts.ignore_tags:
                continue

            if i in SourceConsts.dedupes:
                i = SourceConsts.dedupes[i]
            else:
                i = self._strip_words(strip_words, i)
                i = VideoSource._remove_helper_words(i)

            if i in SourceConsts.ignore_tags:
                continue

            if len(i) >= 3:
                tags.add(i)
                strip_words.append(i)
                if len(i.split(" ")) == 1 and i[-1] == "s":
                    strip_words.append(i[:-1])
                strip_words = sorted(strip_words, key=len, reverse=True)

        for r in range(2):
            tags = self._semantically_update(tags)

        return tags

    def _strip_words(self, words, val):
        for j in words:
            val = re.sub(r"\b" + j + r"\b", "", val)
            val = re.sub(r"\s+", " ", val)
        return val.strip()

    @classmethod
    @cache
    def _remove_helper_words(cls, i):
        for t in ["s", "and", "with", "for", ","]:
            if i.startswith(f"{t} "):
                i = i[len(t) :]
            if i.endswith(f" {t}"):
                i = i[: -len(t)]
            i = i.strip()
        return i

    def _add_from_text(self, text):
        tags = set()
        for i in SourceConsts.possible_tags:
            if i in tags:
                continue
            elif re.search(r"\b" + i + r"\b", text) is not None:
                tags.add(i)
        return tags

    @classmethod
    @cache
    def _semantically_update_tag(cls, tag):
        to_add = set()
        to_remove = set()
        if tag in SourceConsts.expands:
            to_add.update(SourceConsts.expands[tag])
            to_remove.add(tag)
        if tag in SourceConsts.dedupes:
            to_add.add(SourceConsts.dedupes[tag])
            to_remove.add(tag)
        return to_add, to_remove

    def _semantically_update(self, tags):
        to_remove = set()
        to_add = set()
        for tag in tags:
            t_a, t_r = self._semantically_update_tag(tag)
            to_add.update(t_a)
            to_remove.update(t_r)

            if tag.startswith("no ") and tag[3:] in tags:
                to_remove.add(tag[3:])
            if tag.endswith("s") and tag[:-1] in tags:
                to_remove.add(tag[:-1])

        if "no equipment" in tags:
            to_remove.add("weights")

        for k, v in SourceConsts.mappings.items():
            if k in tags and v not in tags:
                to_add.add(v)

        tags.update(to_add)
        tags = tags - to_remove
        return tags
