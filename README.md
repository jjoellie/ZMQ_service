# ZMQ_service

Demonstraties van de vier ZeroMQ berichtpatronen in Python.

```
zeromq_patterns/
├─ part1_req_rep/
│   ├─ client/       client.py  — REQ socket, stuurt naar meerdere servers (1s timeout)
│   └─ server/       server.py  — REP socket, antwoordt met server-ID
│
├─ part2_pub_sub/
│   ├─ sensors/      temperature_sensor.py  — publiceert temperatuurdata (PUB)
│   │                humidity_sensor.py     — publiceert vochtigheidsdata (PUB)
│   ├─ broker/       broker.py  — XSUB/XPUB forwarder
│   └─ dashboard/    dashboard.py  — SUB socket + Tkinter UI
│
├─ part3_push_pull/
│   ├─ logger/       logger.py   — PUSH, stuurt batches log-regels
│   └─ analyzer/     analyzer.py — PULL, analyseert en toont resultaten
│
└─ part4_dealer_router/
    ├─ broker/       broker.py  — ROUTER, beheert chatrooms
    └─ client/       client.py  — DEALER, interactieve chat-client
```

## Installatie

```bash
pip install -r requirements.txt
```

---

## Deel 1 — Request-Reply (req/rep)

De client stuurt een verzoek naar een server. Als er binnen **1 seconde** geen antwoord
komt, probeert de client de volgende server. Elke server vermeldt zijn ID in het antwoord.

**Terminal 1 – servers starten:**
```bash
python zeromq_patterns/part1_req_rep/server/server.py 1 5550
python zeromq_patterns/part1_req_rep/server/server.py 2 5551
python zeromq_patterns/part1_req_rep/server/server.py 3 5552
```

**Terminal 2 – client starten:**
```bash
python zeromq_patterns/part1_req_rep/client/client.py
```

Om timeout-gedrag te demonstreren: start enkel server 2 (poort 5551).
De client zal server 1 proberen, time-outen, dan antwoord krijgen van server 2.

---

## Deel 2 — Publish-Subscribe (pub/sub)

Sensoren publiceren data via een broker. Het dashboard abonneert op een gewenst onderwerp
en toont de meest recente meldingen binnen een instelbaar tijdvenster.

**Terminal 1 – broker:**
```bash
python zeromq_patterns/part2_pub_sub/broker/broker.py
```

**Terminal 2 & 3 – temperatuursensoren:**
```bash
python zeromq_patterns/part2_pub_sub/sensors/temperature_sensor.py 1
python zeromq_patterns/part2_pub_sub/sensors/temperature_sensor.py 2
```

**Terminal 4 – vochtigheidssensor:**
```bash
python zeromq_patterns/part2_pub_sub/sensors/humidity_sensor.py
```

**Terminal 5 – dashboard:**
```bash
python zeromq_patterns/part2_pub_sub/dashboard/dashboard.py
```

In het dashboard kun je via de dropdown kiezen tussen `temperature` en `humidity`,
en het tijdvenster (in seconden) aanpassen.

---

## Deel 3 — Push/Pull (pipeline)

De logger stuurt batches van warning/error logs naar de pipeline.
Meerdere analyzers verwerken de logs parallel (round-robin verdeling).

**Terminal 1 & 2 – analyzers starten (vóór de logger):**
```bash
python zeromq_patterns/part3_push_pull/analyzer/analyzer.py 1
python zeromq_patterns/part3_push_pull/analyzer/analyzer.py 2
```

**Terminal 3 – logger starten:**
```bash
python zeromq_patterns/part3_push_pull/logger/logger.py
```

---

## Deel 4 — Dealer/Router (async chatrooms)

Clients verbinden met de broker en kunnen chatrooms joinen. Berichten worden
doorgestuurd naar alle clients in dezelfde chatroom.

**Terminal 1 – broker:**
```bash
python zeromq_patterns/part4_dealer_router/broker/broker.py
```

**Terminal 2 & 3 – clients:**
```bash
python zeromq_patterns/part4_dealer_router/client/client.py Alice
python zeromq_patterns/part4_dealer_router/client/client.py Bob
```

**Beschikbare commando's in de client:**
```
join  <room>          — join een chatroom
leave <room>          — verlaat een chatroom
msg   <room> <tekst>  — stuur een bericht naar iedereen in de room
rooms                 — toon je huidige rooms
quit                  — afsluiten
```
