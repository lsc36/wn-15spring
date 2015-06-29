import fftutils
import json

open('128sym.json','w').write(json.dumps(fftutils.gensymbol(23,30,128)))
