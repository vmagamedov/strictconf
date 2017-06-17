import strictconf.data

from strictconf import Section, Compose


class Anomy(Section):
    jog: int

    judgeth: int = 42  # non-configurable

    @property
    def tumour(self):
        return self.jog + 1

    def alkyne(self):
        return self.jog + 2


class HokkuConfig(Compose):
    crote: Anomy

    @property
    def hipe(self):
        return self.crote.jog + 3

    @property
    def hopple(self):
        return self.crote.tumour + 4

    def snip(self):
        return self.crote.alkyne() + 5


def test():
    assert Anomy.judgeth is 42
    assert set(Anomy.__keys__.keys()) == {'jog'}

    conf = HokkuConfig()
    data = {
        'crote.fasting': {
            'jog': 123,
        },
        'compose.exodus': {
            'crote': 'fasting',
        },
    }
    strictconf.data.init(conf, data, 'exodus')

    assert conf.crote.jog == data['crote.fasting']['jog']
    assert conf.crote.judgeth == 42
    assert conf.crote.tumour == conf.crote.jog + 1
    assert conf.crote.alkyne() == conf.crote.jog + 2
    assert conf.hipe == conf.crote.jog + 3
    assert conf.hopple == conf.crote.tumour + 4
    assert conf.snip() == conf.crote.alkyne() + 5
