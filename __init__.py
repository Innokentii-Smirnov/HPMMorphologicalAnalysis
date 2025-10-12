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
    
    def __eq__(self, other):
        return (self.segmentation == other.segmentation and
                self.translation == other.translation and
                self.pos == other.pos and
                self.det == other.det)
    
    @property
    def morph_info(self):
        raise NotImplementedError
    
    def __tuple__(self):
        return self.segmentation, self.translation, self.morph_info, self.pos, self.det
    
    def __str__(self):
        return ' @ '.join(self.__tuple__())
    
    def __hash__(self):
        return self.__tuple__().__hash__()
    
    def to_multi(self):
        raise NotImplementedError
        
class SingleMorph(Morph):
    
    def __init__(self,
                 translation: str,
                 segmentation: str,
                 morph_tag: str,
                 pos: str,
                 det: str):
        super().__init__(translation, segmentation, pos, det)
        self.morph_tag = morph_tag
    
    def __eq__(self, other):
        if super().__eq__(other):
            if isinstance(other, MultiMorph):
                if other.is_singletone:
                    return self.morph_tag == next(iter(other.morph_tags.values()))
                else:
                    return false
            else:
                return self.morph_tag == other.morph_tag
        else:
            return false
    
    @property
    def morph_info(self):
        return self.morph_tag
    
    def __hash__(self):
        return self.__tuple__().__hash__()
        
    def to_multi(self):
        return MultiMorph(self.segmentation, self.translation,
            {'a': self.morph_tag}, self.pos, self.det)

class MultiMorph(Morph):
    
    def __init__(self,
                 translation: str,
                 segmentation: str,
                 morph_tags: dict[str, str],
                 pos: str,
                 det: str):
        super().__init__(translation, segmentation, pos, det)
        self.morph_tags = morph_tags
    
    def __eq__(self, other):
        if super().__eq__(other):
            if isinstance(other, SingleMorph):
                return self.is_singletone and next(iter(self.morph_tags.values())) == other.morph_tag
            else:
                return self.morph_tags == other.morph_tags
        else:
            return false
    
    @property
    def morph_info(self) -> str:
        elements = list[str]()
        for key, value in self.morph_tags.items():
            element = '{ ' + key + '  → ' + value + '}'
            elements.append(element)
        return ''.join(elements)
    
    @property
    def is_singletone(self):
        return len(self.morph_tags) == 1
    
    def to_single(self):
        return SingleMorph(self.segmentation, self.translation,
            next(iter(self.morph_tags.values())), self.pos, self.det)
    
    def __hash__(self):
        if (self.is_singletone):
            return self.to_single().__hash__()
        else:
            return self.__tuple__().__hash__()
    
    def to_multi(self):
        return self
        
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

def parseMorph(string: str) -> Morph:
    try:
        translation, segmentation, morph_info, pos, det = list(map(str.strip, string.split('@')))
    except ValueError:
        raise ValueError(string)
    if in_braces(morph_info):
        morph_tags = parseMorphTags(morph_info)
        return MultiMorph(translation, segmentation, morph_tags, pos, det)
    else:
        return SingleMorph(translation, segmentation, morph_info, pos, det)
