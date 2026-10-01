from nbs_bl.configuration import load_and_configure_everything

load_and_configure_everything()

RE(psh10.open())
RE(psh7.open())
manipz.velocity.set(100)
RE(mv(manipz, 364))
manipz.velocity.set(1)
