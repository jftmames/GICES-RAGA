import json, pathlib, statistics
from pathlib import Path

def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def cite(ids: list[str]):
    # carga el pequeño índice y devuelve solo las entradas pedidas
    idx = [json.loads(l) for l in Path("rag/index.jsonl").read_text(encoding="utf-8").splitlines()]
    by_id = {x["id"]: x for x in idx}
    return [by_id[i] for i in ids if i in by_id]

def compute_kpis():
    # E1
    e1 = load_json("data/normalized/energy_2024-01.json")
    total_co2e = round(sum(r["kwh"]*r.get("emission_factor_co2e",0.23) for r in e1)/1000.0, 3)

    # S1
    s1 = load_json("data/normalized/hr_2024-01.json")
    s1r = s1[0] if s1 else {"employees_start":0,"employees_end":0,"exits":0}
    avg_emp = (s1r["employees_start"] + s1r["employees_end"])/2 or 1
    turnover = round(s1r["exits"]/avg_emp, 4)

    # G1
    g1 = load_json("data/normalized/ethics_2024-01.json")
    g1r = g1[0] if g1 else {"cases_closed":0,"closed_with_resolution":0}
    pct_resolution = round((g1r["closed_with_resolution"]/(g1r["cases_closed"] or 1))*100, 2)

    return {
        "E1-1.total_co2e_tons": total_co2e,
        "S1-1.employee_turnover": turnover,
        "G1-1.resolution_rate_pct": pct_resolution
    }

def explain(kpis: dict):
    return {
      "E1-1.total_co2e_tons": {
        "hypothesis": "Σ(kWh_i * emission_factor_i)/1000",
        "evidence": ["data/normalized/energy_2024-01.json","ontology/validation.log"],
        "citations": cite(["ESRS_E1_DR1"]),
        "residual": 0.0
      },
      "S1-1.employee_turnover": {
        "hypothesis": "exits / mean(employees_start, employees_end)",
        "evidence": ["data/normalized/hr_2024-01.json","ontology/validation.log"],
        "citations": cite(["ESRS_S1_DR1"]),
        "residual": 0.0
      },
      "G1-1.resolution_rate_pct": {
        "hypothesis": "closed_with_resolution / cases_closed * 100",
        "evidence": ["data/normalized/ethics_2024-01.json","ontology/validation.log"],
        "citations": cite(["ESRS_G1_DR1"]),
        "residual": 0.0
      }
    }

def main():
    kpis = compute_kpis()
    Path("raga").mkdir(exist_ok=True)
    Path("raga/kpis.json").write_text(json.dumps(kpis, indent=2, ensure_ascii=False))
    Path("raga/explain.json").write_text(json.dumps(explain(kpis), indent=2, ensure_ascii=False))
    print("RAGA OK → raga/kpis.json, raga/explain.json")

if __name__ == "__main__":
    main()
