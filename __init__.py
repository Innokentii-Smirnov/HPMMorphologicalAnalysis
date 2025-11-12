from __future__ import annotations
from logging import getLogger
logger = getLogger(__name__)

class Morph:

    def __init__(self,
                 segmentation: str,
                 translation: str,
                 pos: str,
                 det: str):
        self.segmentation = segmentation
        self.translation = translation
        self.pos = pos
        self.det = det
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        return (self.segmentation == other.segmentation and
                self.translation == other.translation and
                self.pos == other.pos and
                self.det == other.det)
    
    @property
    def morph_info(self) -> str:
        raise NotImplementedError
    
    def __tuple__(self) -> tuple[str, str, str, str, str]:
        return self.segmentation, self.translation, self.morph_info, self.pos, self.det
    
    def __str__(self) -> str:
        return ' @ '.join(self.__tuple__())
    
    def __hash__(self) -> int:
        return self.__tuple__().__hash__()
    
    def to_multi(self) -> MultiMorph:
        raise NotImplementedError

    """Return the morphological tag if it is the only morphological tag option
    for this analysis. Log a warning if a morphological tag index
    is requiered by the analysis' type (but not specified).
    If the analysis has multiple options, log an error and return None.
    :return: The morphological tag if the morphological analysis contains
    exactly one morphological tag option, None otherwise.
    """
    @property
    def single_morph_tag(self) -> str | None:
      raise NotImplementedError

    """Return the morphological with the specified index.
    Log a warning if the analysis does not support multiple
    morphological tag options and an error if the index
    does not occur in the dictionary containing the
    morphological tag options for this analysis.
    :return: The morphological analysis with the specified index
    if the index is found or the only morphological tag if the analysis
    does not support multiple options, None otherwise.
    """
    def __getitem__(self, index: str) -> str | None:
      raise NotImplementedError

    @classmethod
    def parse(cls, string: str) -> Morph:
      try:
          translation, segmentation, morph_info, pos, det = list(map(str.strip, string.split('@')))
      except ValueError:
          raise ValueError(string)
      if in_braces(morph_info):
          morph_tags = parseMorphTags(morph_info)
          return MultiMorph(translation, segmentation, morph_tags, pos, det)
      else:
          return SingleMorph(translation, segmentation, morph_info, pos, det)
        
class SingleMorph(Morph):
    
    def __init__(self,
                 translation: str,
                 segmentation: str,
                 morph_tag: str,
                 pos: str,
                 det: str):
        super().__init__(translation, segmentation, pos, det)
        self.morph_tag = morph_tag
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        if super().__eq__(other):
            if isinstance(other, MultiMorph):
                if other.is_singletone:
                    return self.morph_tag == next(iter(other.morph_tags.values()))
                else:
                    return False
            elif isinstance(other, SingleMorph):
                return self.morph_tag == other.morph_tag
            else:
                return NotImplemented
        else:
            return False
    
    @property
    def morph_info(self) -> str:
        return self.morph_tag
    
    def __hash__(self) -> int:
        return self.__tuple__().__hash__()
        
    def to_multi(self) -> MultiMorph:
        return MultiMorph(self.segmentation, self.translation,
            {'a': self.morph_tag}, self.pos, self.det)

    @property
    def single_morph_tag(self) -> str:
      return self.morph_tag

    def __getitem__(self, index: str) -> str:
      logger.warning('A morphological tag index (%s) is specified for a morphological analysis which does not support multiple morphological tag options (%s). The single available morphologial tag will be used.',
                     index, self)
      return self.morph_tag

class MultiMorph(Morph):
    
    def __init__(self,
                 translation: str,
                 segmentation: str,
                 morph_tags: dict[str, str],
                 pos: str,
                 det: str):
        super().__init__(translation, segmentation, pos, det)
        self.morph_tags = morph_tags
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morph):
          return NotImplemented
        if super().__eq__(other):
            if isinstance(other, SingleMorph):
                return self.is_singletone and next(iter(self.morph_tags.values())) == other.morph_tag
            elif isinstance(other, MultiMorph):
                return self.morph_tags == other.morph_tags
            else:
                return NotImplemented
        else:
            return False
    
    @property
    def morph_info(self) -> str:
        elements = list[str]()
        for key, value in self.morph_tags.items():
            element = '{ ' + key + '  → ' + value + '}'
            elements.append(element)
        return ''.join(elements)
    
    @property
    def is_singletone(self) -> bool:
        return len(self.morph_tags) == 1
    
    def to_single(self) -> SingleMorph:
        return SingleMorph(self.segmentation, self.translation,
            next(iter(self.morph_tags.values())), self.pos, self.det)
    
    def __hash__(self) -> int:
        if (self.is_singletone):
            return self.to_single().__hash__()
        else:
            return self.__tuple__().__hash__()
    
    def to_multi(self) -> MultiMorph:
        return self

    @property
    def single_morph_tag(self) -> str | None:
      if self.is_singletone:
        logger.warning('No morphological tag index is specified for a morphological analysis supporting multiple morphological tag options (%s). The single available option will be used.', self)
        return next(iter(self.morph_tags.values()))
      else:
        logger.error('No morphological tag index is specified for a morphological analysis supporting multiple morphological tag options (%s). Because of ambiguity, no morphological tag option will be used.', self)
        return None

    def __getitem__(self, index: str) -> str | None:
      if index in self.morph_tags:
        return self.morph_tags[index]
      else:
        logger.error('The specified morphological tag index (%s) was not found in the morphological tag option dictionary of the morphological analysis (%s). No morphological tag option will be used.', index, self)
        return None
        
def in_braces(string: str) -> bool:
    return string.startswith('{') and string.endswith('}')

def parseMorphTags(string: str) -> dict[str, str]:
    morph_tags = dict[str, str]()
    elements = string[1:-1].split('{')
    for element in elements:
        element = element.strip().removesuffix('}')
        try:
            key, value = list(map(str.strip, element.split('→')))
        except:
            raise ValueError(string)
        morph_tags[key] = value
    return morph_tags
