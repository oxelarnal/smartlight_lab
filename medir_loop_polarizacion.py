# medir_loop.py — proceso persistente dentro del SmartLight
# Se lanza UNA VEZ vía SSH y se queda escuchando comandos en stdin/stdout

import sys, json, pathlib, time
import yaml
import logging
import logging.config
from pathlib import Path
from smartlight import Smartlight

# ── Parámetros fijos ────────────────────────────────────────────────────
ACTIVE_PORTS = list(range(0, 22)) + list(range(34, 40))   # 28 puertos
RETOS_DIR    = pathlib.Path('retos_v6')

# ── Rutas maestras del Anillo Isotrópico ─────────────────────────────────
RUTAS = {
    0:  [(0,'x'),(6,'x'),(10,'x'),(16,'x'),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    1:  [(0,'='),(6,'x'),(10,'x'),(16,'x'),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    2:  [(9,'x'),(10,'='),(16,'x'),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    3:  [(15,'x'),(19,'='),(20,'x'),(21,'='),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    4:  [(15,'x'),(9,'='),(10,'='),(16,'x'),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    5:  [(19,'x'),(20,'x'),(21,'='),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    6:  [(28,'x'),(29,'x'),
         (30,'x'),(31,1-1/6),(36,1-1/5),(41,1-1/4),(40,1-1/3),(35,1-1/2)],
    7:  [(34,'x'),(38,'='),(39,'x'),
         (35,'x'),(30,1-1/6),(31,1-1/5),(36,1-1/4),(41,1-1/3),(40,1-1/2)],
    8:  [(34,'x'),(28,'='),(29,'x'),
         (30,'x'),(31,1-1/6),(36,1-1/5),(41,1-1/4),(40,1-1/3),(35,1-1/2)],
    9:  [(38,'x'),(39,'x'),
         (35,'x'),(30,1-1/6),(31,1-1/5),(36,1-1/4),(41,1-1/3),(40,1-1/2)],
    10: [(47,'='),(44,'x'),(39,'x'),
         (35,'x'),(30,1-1/6),(31,1-1/5),(36,1-1/4),(41,1-1/3),(40,1-1/2)],
    11: [(53,'x'),(57,'='),(58,'='),(54,'x'),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    12: [(53,'x'),(47,'='),(48,'x'),(49,'='),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    13: [(57,'x'),(58,'='),(54,'x'),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    14: [(66,'='),(63,'x'),(58,'x'),(54,'x'),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    15: [(66,'x'),(63,'x'),(58,'x'),(54,'x'),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    16: [(67,'x'),(63,'='),(58,'x'),(54,'x'),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    17: [(68,'x'),(64,'='),(59,'x'),(54,'='),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    18: [(69,'x'),(64,'x'),(59,'x'),(54,'='),(49,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    19: [(70,'x'),(65,'='),(61,'x'),(55,'x'),(50,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    20: [(71,'x'),(65,'x'),(61,'x'),(55,'x'),(50,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    21: [(71,'='),(65,'x'),(61,'x'),(55,'x'),(50,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    22: [(62,'x'),(61,'='),(55,'x'),(50,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    23: [(56,'x'),(52,'='),(51,'x'),(50,'='),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    24: [(56,'x'),(62,'='),(61,'='),(55,'x'),(50,'x'),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    25: [(52,'x'),(51,'x'),(50,'='),(45,'x'),
         (40,'x'),(35,1-1/6),(30,1-1/5),(31,1-1/4),(36,1-1/3),(41,1-1/2)],
    26: [(43,'x'),(42,'x'),
         (41,'x'),(40,1-1/6),(35,1-1/5),(30,1-1/4),(31,1-1/3),(36,1-1/2)],
    27: [(37,'x'),(33,'='),(32,'x'),
         (36,'x'),(41,1-1/6),(40,1-1/5),(35,1-1/4),(30,1-1/3),(31,1-1/2)],
    28: [(37,'x'),(43,'='),(42,'x'),
         (41,'x'),(40,1-1/6),(35,1-1/5),(30,1-1/4),(31,1-1/3),(36,1-1/2)],
    29: [(33,'x'),(32,'x'),
         (36,'x'),(41,1-1/6),(40,1-1/5),(35,1-1/4),(30,1-1/3),(31,1-1/2)],
    30: [(24,'='),(27,'x'),(32,'x'),
         (36,'x'),(41,1-1/6),(40,1-1/5),(35,1-1/4),(30,1-1/3),(31,1-1/2)],
    31: [(18,'x'),(14,'='),(13,'='),(17,'x'),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    32: [(18,'x'),(24,'x'),(27,'x'),(32,'x'),
         (36,'x'),(41,1-1/6),(40,1-1/5),(35,1-1/4),(30,1-1/3),(31,1-1/2)],
    33: [(14,'x'),(13,'='),(17,'x'),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    34: [(5,'='),(8,'x'),(13,'x'),(17,'x'),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    35: [(5,'x'),(8,'x'),(13,'x'),(17,'x'),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    36: [(4,'x'),(8,'='),(13,'x'),(17,'x'),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    37: [(3,'x'),(7,'='),(12,'x'),(17,'='),(22,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    38: [(2,'x'),(7,'='),(11,'x'),(16,'='),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
    39: [(1,'x'),(6,'='),(10,'x'),(16,'x'),(21,'x'),(26,'x'),
         (31,'x'),(36,1-1/6),(41,1-1/5),(40,1-1/4),(35,1-1/3),(30,1-1/2)],
}

# ── Configuración de logging ──────────────────────────────────────────
config = yaml.safe_load(Path("logging.yaml").read_text())
logging.config.dictConfig(config)

# ── Conectar UNA SOLA VEZ ─────────────────────────────────────────────
sys.stderr.write('Conectando al chip...\n')
sys.stderr.flush()

sl = Smartlight()
try:
    sl.disconnect()
except Exception:
    pass
sl.connect()
sl.calibration()
sl.reset_mesh()

sys.stderr.write('✓ Chip conectado y calibrado.\n')
sys.stderr.flush()

# ── Caché de retos cargados por puerto ────────────────────────────────
cache_retos = {}   # inport -> (challenges, route_pucs, dynamic_pucs, outports)

def cargar_retos(inport):
    if inport in cache_retos:
        return cache_retos[inport]

    # ── Configurar puerto de entrada y monitorización ──────────────────
    sl.set_input_port(inport)
    sl.enable_internal_monitoring()

    fname = RETOS_DIR / f'challenges_ring_port{inport:02d}.json'
    with open(fname) as f:
        d = json.load(f)

    challenges        = [{int(k): v for k, v in ch.items()}
                         for ch in d['challenges']]
    route_pucs_inport = set(d['route_pucs'])
    dynamic_pucs      = d['dynamic_pucs']
    outports          = [p for p in ACTIVE_PORTS if p != inport]

    solapamiento = route_pucs_inport & set(int(k) for k in challenges[0].keys())
    assert not solapamiento, f'⚠ Solapamiento: {solapamiento}'

    sys.stderr.write(f'✓ Retos cargados para puerto {inport} — sin solapamiento\n')
    sys.stderr.flush()

    cache_retos[inport] = (challenges, route_pucs_inport, dynamic_pucs, outports)
    return cache_retos[inport]

# ── Programar ruta con CFs exactos ─────────────────────────────────────
def programar_ruta(inport, route_pucs):
    puc_conf = []
    for puc, estado in RUTAS[inport]:
        if estado == 'x':
            puc_conf.append((puc, [1.0, 0.0]))
        elif estado == '=':
            puc_conf.append((puc, [0.0, 0.0]))
        else:
            puc_conf.append((puc, [float(estado), 0.0]))
    sl.reset_puc(pucs_id=list(route_pucs))
    sl.set_coupling_factor_phase(puc_conf_info=puc_conf)

# ── Bucle principal — escucha comandos por stdin ────────────────────────
# ENTRADA medida normal:    {"inport": 21, "n_retos": 50}
# ENTRADA preparar_externo: {"accion": "preparar_externo", "inport": 21, "outport": 3}
# ENTRADA polarizacion:     {"accion": "polarizacion", "inport": 21, "outport": 3}
# SALIDA:  {"inport": 21, "outports": [...], "n_medidos": 50, "powers": [ {...}, ... ]}

sys.stderr.write('Listo. Esperando comandos...\n')
sys.stderr.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    if line == 'EXIT':
        break

    try:
        cmd    = json.loads(line)
        accion = cmd.get('accion', 'medir')

        # ── PREPARAR MONITORIZACIÓN EXTERNA (ajuste manual con medidor analógico) ──
        if accion == 'preparar_externo':
            inport         = cmd['inport']
            outport_prueba = cmd['outport']

            sl.reset_mesh()
            sl.set_input_port(inport)
            sl.enable_external_monitoring([outport_prueba])
            sl.interconnect_auto(inport, outport_prueba)

            respuesta = {
                'accion':         'preparar_externo',
                'inport':         inport,
                'outport_prueba': outport_prueba,
                'status':         'listo — mide con el medidor analógico y ajusta la polarización',
            }
            print(json.dumps(respuesta))
            sys.stdout.flush()
            continue

        # ── COMPROBAR POLARIZACIÓN (fotodetectores internos) ────────────
        if accion == 'polarizacion':
            inport         = cmd['inport']
            outport_prueba = cmd['outport']
            outports_full  = [p for p in ACTIVE_PORTS if p != inport]

            sl.reset_mesh()
            sl.set_input_port(inport)
            sl.enable_internal_monitoring([outport_prueba])
            sl.interconnect_auto(inport, outport_prueba)
            powers = sl.get_output_power(inport=inport, outport=outports_full)

            respuesta = {
                'accion':         'polarizacion',
                'inport':         inport,
                'outport_prueba': outport_prueba,
                'powers':         {str(k): v for k, v in powers.items()},
            }
            print(json.dumps(respuesta))
            sys.stdout.flush()
            continue

        # ── MEDIDA NORMAL ────────────────────────────────────────────────
        inport   = cmd['inport']
        n_retos  = cmd['n_retos']

        challenges, route_pucs_inport, dynamic_pucs, outports = cargar_retos(inport)
        powers_list = []

        for reto in challenges[:n_retos]:
            # 1. Programar ruta con CFs exactos
            programar_ruta(inport, route_pucs_inport)

            # 2. Aplicar fases aleatorias en TBUs dinámicas
            sl.set_driven_phases(reto, compensate_passive_phase=False)

            # 3. Leer potencias de salida
            powers = sl.get_output_power(inport=inport, outport=outports)
            powers_list.append({str(k): v for k, v in powers.items()})

        respuesta = {
            'inport':    inport,
            'outports':  outports,
            'n_medidos': len(powers_list),
            'powers':    powers_list,
        }
        print(json.dumps(respuesta))
        sys.stdout.flush()

    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.stdout.flush()

# ── Desconectar al salir ─────────────────────────────────────────────
sl.reset_mesh()
sl.disconnect()
sys.stderr.write('✓ Chip desconectado correctamente.\n')
