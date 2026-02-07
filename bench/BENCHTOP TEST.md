# Benchtop TEG Test - 220V Lab Scale
Power Budget (220V @ 20A = 4.4 kW available)
Component	Power Draw
Oil heater	2.0 kW
Recirculating chiller	0.8 kW
Pumps, controls	0.3 kW
Total	3.1 kW
Available for expansion	1.3 kW
Minimum Test Configuration


BENCHTOP TEST - SINGLE SANDWICH SLICE

          1 or 2 PowerCards (16-32 TEGs)
          ~150-300W electrical output
          ~1.6-3.2 kW thermal input
          
    ┌─────────────────────────────────────┐
    │         Cold HX (Aluminum)          │  ← Chiller loop
    ├─────────────────────────────────────┤
    │         TIM (Silicone pad)          │
    ├─────────────────────────────────────┤
    │    PowerCard #1 (16 TEGs) ▓▓▓▓▓     │  ← ~147W output
    ├─────────────────────────────────────┤
    │         TIM (Graphite)              │
    ╠═════════════════════════════════════╣
    ║    HOT HEAT EXCHANGER (Center)      ║  ← Oil loop (400°C)
    ╠═════════════════════════════════════╣
    │         TIM (Graphite)              │
    ├─────────────────────────────────────┤
    │    PowerCard #2 (16 TEGs) ▓▓▓▓▓     │  ← ~147W output
    ├─────────────────────────────────────┤
    │         TIM (Silicone pad)          │
    ├─────────────────────────────────────┤
    │         Cold HX (Aluminum)          │  ← Chiller loop
    └─────────────────────────────────────┘
    
    Total: 32 TEGs / ~294W output
    Footprint: ~200mm × 180mm × 100mm






Equipment - Off-the-Shelf 220V
Item	Model/Type	Specs	Est. Cost
Oil Heater	Lab recirculating heater	2 kW, 400°C max, 220V	$2,500-4,000
Chiller	Lab recirculating chiller	1 kW cooling, 220V	$1,500-2,500
Load	DC electronic load	500W, 0-60V	$300-500
Example Equipment:
Component	Specific Model	Price
Oil heater	Julabo SE-12 (12L, 300°C)	$3,200
Oil heater	Huber Unistat 405 (5L, 400°C)	$8,000
Oil heater	PolyScience AD15H-40 (15L, 400°C)	$4,500
Chiller	Julabo FL300 (300W @ 20°C)	$1,800
Chiller	PolyScience 6160 (1.5kW @ 20°C)	$2,200
Chiller	Thermo Neslab ThermoFlex 2500	$3,500
Complete Benchtop BOM
Option A: Minimum (16 TEGs, ~150W)
Item	Qty	Cost	Notes
Equipment			
Thermal oil heater (2kW, 400°C)	1	$4,500	PolyScience or equiv
Recirculating chiller (1kW)	1	$2,200	
DC electronic load	1	$400	
Test Article			
Alphabet PowerCard	1	$65	From stock
Hot HX block (machined SS)	1	$350	Single-sided for min test
Cold HX block (machined Al)	1	$150	
Graphite TIM	2	$5	
Silicone thermal pad	2	$2	
Clamp assembly	1	$80	Bolted compression
Instrumentation			
Thermocouples	6	$90	Type K
DAQ module	1	$200	USB thermocouple reader
DC voltmeter/ammeter	1	$50	
Misc			
Fittings, tubing	1 lot	$150	High-temp silicone
Insulation	1 lot	$50	Ceramic fiber
Thermal oil (1 gal)	1	$80	Duratherm 600
TOTAL		$8,372	
Option B: Sandwich Test (32 TEGs, ~294W)
Item	Qty	Cost	Notes
Equipment			
Thermal oil heater (2kW, 400°C)	1	$4,500	
Recirculating chiller (1.5kW)	1	$2,500	Slightly larger
DC electronic load	1	$400	
Test Article			
Alphabet PowerCard	2	$130	From stock
Hot HX block (machined SS)	1	$450	Double-sided
Cold HX blocks (machined Al)	2	$300	Top and bottom
Graphite TIM	4	$10	
Silicone thermal pad	4	$4	
Through-bolt clamp assembly	1	$120	Full sandwich test
Instrumentation			
Thermocouples	10	$150	Type K
DAQ module	1	$200	
DC voltmeter/ammeter	1	$50	
Misc			
Fittings, tubing	1 lot	$200	
Insulation	1 lot	$80	
Thermal oil (1 gal)	1	$80	
TOTAL		$9,174	
What Each Test Validates
Aspect	Min (16 TEG)	Sandwich (32 TEG)
TEG performance @ 400°C	✅	✅
Thermal oil compatibility	✅	✅
TIM performance	✅	✅
Heat flux through stack	✅	✅
Double-sided hot HX	❌	✅
Sandwich clamping	❌	✅
Thermal symmetry	❌	✅
Power prediction accuracy	✅	✅
Comparison: Benchtop vs Full Prototype
Parameter	Benchtop (32 TEG)	Single-Pair (320 TEG)
Power output	294 W	2,900 W
Thermal input	3.2 kW	32 kW
Equipment power	220V / 20A	480V / 60A
Cost	$9,174	$8,414 + lab equipment
Space	Desktop	1.5m × 0.8m floor
Build time	1-2 weeks	6-7 weeks
Test time	2-4 weeks	8 weeks
Validates sandwich?	✅ Yes	✅ Yes
Validates tower stacking?	❌ No	✅ Yes
Validates shared cold HX?	❌ No	✅ Yes



PHASE 0: BENCHTOP (You Are Here)
│
│  32 TEGs / 294W / $9,174 / 4-6 weeks
│  - Validate sandwich concept
│  - Validate 400°C operation
│  - Validate TEG performance
│
▼
PHASE 1: SINGLE-PAIR PROTOTYPE
│
│  320 TEGs / 2.9kW / $8,414 / 17 weeks
│  - Validate tower assembly
│  - Validate shared cold HX
│  - 1000-hour endurance
│
▼
PHASE 2: 8-PAIR CONTAINER
│
│  2,560 TEGs / 24kW / $105,134
│  - Full deployment
│
▼
PHASE 3: QUAD-BLOCK (if reliable)
│
│  3,840 TEGs / 35kW
│  - Maximum density

BENCHTOP TEST ASSEMBLY - TOP VIEW

    ┌─────────────────────────────────────────────┐
    │                                             │
    │    Oil Heater          Chiller              │
    │    ┌───────┐          ┌───────┐             │
    │    │ 400°C │          │  20°C │             │
    │    │  2kW  │          │  1kW  │             │
    │    └───┬───┘          └───┬───┘             │
    │        │                  │                 │
    │        ▼                  ▼                 │
    │    ┌─────────────────────────┐              │
    │    │                         │              │
    │    │   ┌─────────────────┐   │              │
    │    │   │   TEST STACK    │   │   DC Load   │
    │    │   │   32 TEGs       │───┼──→  300W    │
    │    │   │   ~294W         │   │              │
    │    │   └─────────────────┘   │              │
    │    │                         │              │
    │    │     Clamp Frame         │              │
    │    └─────────────────────────┘              │
    │                                             │
    │              DAQ / Laptop                   │
    │                                             │
    └─────────────────────────────────────────────┘
    
    Bench space: ~1m × 0.6m