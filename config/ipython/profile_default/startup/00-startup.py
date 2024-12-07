import nslsii
from nbs_bl.configuration import load_and_configure_everything
from bluesky.plan_stubs import mv as _mv, mvr as _mvr

load_and_configure_everything()

nslsii.configure_base(
    get_ipython().user_ns, "nbs", publish_documents_with_kafka=False, bec=False
)


def mv(*args, group=None, **kwargs):
    yield from _mv(*args, group=group, **kwargs)


def mvr(*args, group=None, **kwargs):
    yield from _mvr(*args, group=group, **kwargs)


move = mv

RE(psh10.open())
RE(psh7.open())
manipz.velocity.set(100)
RE(mv(manipz, 464))
manipz.velocity.set(1)
