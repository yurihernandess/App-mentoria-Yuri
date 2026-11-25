PROJECT = 'obras'; HOOK = 'big'; HOOK_UNTIL = 2.8; END = 'cfg'
CHIP = {'big': 'COMO ESTÃO\nAS OBRAS?', 'sub': 'ROGGA · PENHA · PIÇARRAS · BARRA VELHA'}
def P(name, dur, a, b, lab=None, title=None, trans='whip'):
    d = dict(photo=name, dur=dur, a=a, b=b, trans=trans)
    if title: d['label'] = (lab, title)
    return d
TIMELINE = [
    # PENHA
    P('LS_1004', 2.8, (0.62, .5, 1.15), (0.42, .5, 1.0)),
    P('LS_1002', 2.0, (0.22, .5, 1.0), (0.5, .5, 1.05), 'PENHA · OUT/2026', 'LANDSCAPE'),
    P('LS_1005', 1.6, (0.4, .5, 1.1), (0.6, .5, 1.0)),
    P('MS_1001', 2.0, (0.78, .5, 1.0), (0.55, .5, 1.05), 'PENHA · OUT/2026', 'MORADA\nDO SOL'),
    P('BA_1001', 2.0, (0.3, .5, 1.0), (0.55, .5, 1.08), 'PENHA · OUT/2026', 'BAÍA AZUL'),
    # BALNEARIO PICARRAS
    P('BE_1013', 2.2, (0.5, .5, 1.15), (0.5, .5, 1.0), 'BALNEÁRIO PIÇARRAS · OUT/2026', 'BELVEDERE'),
    P('BE_1014', 1.6, (0.45, .5, 1.0), (0.6, .5, 1.08)),
    P('MA_1004', 2.0, (0.38, .5, 1.0), (0.52, .5, 1.1), 'BALNEÁRIO PIÇARRAS · OUT/2026', 'MAUI'),
    P('MA_1013', 1.5, (0.5, .5, 1.0), (0.5, .5, 1.15)),
    P('IB_1003', 2.0, (0.4, .5, 1.05), (0.55, .5, 1.0), 'BALNEÁRIO PIÇARRAS · OUT/2026', 'IBIZA'),
    P('CU_1003', 2.0, (0.3, .5, 1.0), (0.62, .5, 1.0), 'BALNEÁRIO PIÇARRAS · OUT/2026', 'CURAÇAO'),
    P('AR_1004', 2.0, (0.5, .5, 1.12), (0.55, .5, 1.0), 'BALNEÁRIO PIÇARRAS · OUT/2026', 'ARUBA'),
    # BARRA VELHA
    P('FB_1002', 2.4, (0.68, .5, 1.0), (0.62, .5, 1.12), 'BARRA VELHA · OUT/2026', 'FAROL\nDA BARRA'),
    P('FB_1008', 1.7, (0.42, .5, 1.1), (0.5, .5, 1.0)),
    P('FB_1005', 1.9, (0.35, .5, 1.0), (0.55, .5, 1.08)),
]
END_CFG = dict(bg='jpg/FB_1002.jpg', badge='ACOMPANHAMENTO DE OBRA', kicker='ROGGA · LITORAL NORTE DE SC · OUT/2026',
               title='COMPRE NA PLANTA\nVENDO A OBRA AVANÇAR', big='9 OBRAS', big_size=130, sub='PENHA · PIÇARRAS · BARRA VELHA',
               cta='QUERO CONHECER', legal='Imagens: acompanhamento de obra Rogga, outubro/2026.')
