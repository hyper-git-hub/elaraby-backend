from modeltranslation.translator import translator, TranslationOptions
from .models import Options

#Translation Handler Class
class GlobalTranslations(TranslationOptions):
    fields = ('label',)
translator.register(Options, GlobalTranslations)

