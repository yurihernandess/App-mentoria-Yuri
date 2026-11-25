PROJECT = 'joinville'; HOOK = 'big'; HOOK_UNTIL = 2.8; END = 'cfg'
CHIP = {'big': 'COMO ESTÃO\nAS OBRAS?', 'sub': 'ROGGA EM JOINVILLE · OUT/2026'}
def P(name, dur, a, b, lab=None, title=None, trans='whip'):
    d = dict(photo=name, dur=dur, a=a, b=b, trans=trans)
    if title: d['label'] = (lab, title)
    return d
J = 'JOINVILLE · OUT/2026'
TIMELINE = [
    P('AZ_1001', 2.8, (0.55, .5, 1.15), (0.38, .5, 1.0)),
    P('AZ_1003', 2.0, (0.45, .5, 1.0), (0.6, .5, 1.06), J, 'URBAN\nAZALÉIA'),
    P('BV_1001', 2.0, (0.55, .5, 1.12), (0.55, .5, 1.0), J, 'URBAN\nBAVIERA'),
    P('BV_1004', 1.6, (0.45, .5, 1.0), (0.52, .5, 1.1)),
    P('EV_1008', 2.0, (0.5, .5, 1.0), (0.65, .5, 1.08), J, 'EVOLUTION'),
    P('EV_1010', 1.6, (0.5, .5, 1.12), (0.5, .5, 1.0)),
    P('FL_1001', 2.0, (0.3, .5, 1.0), (0.48, .5, 1.06), J, 'FLORATTA'),
    P('FL_1003', 1.6, (0.6, .5, 1.05), (0.5, .5, 1.0)),
    P('PO_1001', 2.0, (0.42, .5, 1.0), (0.56, .5, 1.08), J, 'POLINÉSIA'),
    P('PO_1004', 1.6, (0.4, .5, 1.1), (0.5, .5, 1.0)),
    P('TG_1013', 2.2, (0.32, .5, 1.0), (0.68, .5, 1.0), J, 'TORRES\nDO GLÓRIA'),
    P('TG_1006', 1.8, (0.45, .5, 1.12), (0.45, .5, 1.0)),
]
END_CFG = dict(bg='jpg/AZ_1001.jpg', badge='ACOMPANHAMENTO DE OBRA', kicker='ROGGA · JOINVILLE · OUT/2026',
               title='COMPRE NA PLANTA\nVENDO A OBRA AVANÇAR', big='6 OBRAS', big_size=130, sub='EM ANDAMENTO EM JOINVILLE',
               cta='QUERO CONHECER', legal='Imagens: acompanhamento de obra Rogga, outubro/2026.')
