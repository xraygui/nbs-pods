import nslsii
from nbs_bl.configuration import load_and_configure_everything

load_and_configure_everything()

nslsii.configure_base(
    get_ipython().user_ns, "nbs", publish_documents_with_kafka=False, bec=False
)

RE(psh10.open())
RE(psh7.open())
manipz.velocity.set(100)
RE(mv(manipz, 464))
manipz.velocity.set(1)
