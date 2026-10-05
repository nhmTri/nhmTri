<img src="header.svg" alt="Nguyen Hoang Minh Tri — Operations Data Analyst" width="100%">

**Operations Data Analyst at NielsenIQ.** I work on the part of analytics most people skip: deciding whether a number is allowed to leave the building.

At NielsenIQ I own the quality gate every project passes before hand-over — the rules, the thresholds, and the Python/VBA suite that runs them at 20%, 50% and 90% of fieldwork. In 11 months: **41,037 samples checked**, minor error **6% → 2%**, major error held at a **0.2% median against a 5% ceiling**, project issue rate **−30%**.

Outside work I build the pipelines behind the analysis — Spark at 10M rows, Kafka streaming, fraud rule design, portfolio analytics.


<p align="center">
  <a href="https://nhmtri.github.io/">
    <img src="assets/site-card.svg" width="86%"
         alt="A browser window showing nhmtri.github.io: the portfolio of Nguyen Hoang Minh Tri, with the quality gate, three project cards and a button reading open the live site">
  </a>
</p>

<p align="center">
  <sub><b>The whole thing is at <a href="https://nhmtri.github.io/">nhmtri.github.io</a></b> — the quality gate, the field-work story told through one interviewer, and seven projects with their diagrams and their numbers.</sub>
</p>

---

**Now** · data quality rules, automation, agentic AI workflows
**Next** · credit risk and payments analytics

![RBAC](https://img.shields.io/badge/Top%2015-RMIT%20Business%20Analytics%20Champion%202025-B02E2D?style=flat-square)

![SQL](https://img.shields.io/badge/SQL-window%20functions-184F95?style=flat-square&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-pandas%20·%20scikit--learn-184F95?style=flat-square&logo=python&logoColor=white)
![Spark](https://img.shields.io/badge/Spark-PySpark%20·%20Streaming-184F95?style=flat-square&logo=apachespark&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-streaming-184F95?style=flat-square&logo=apachekafka&logoColor=white)
![Cassandra](https://img.shields.io/badge/Cassandra-raw%20layer-B02E2D?style=flat-square&logo=apachecassandra&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-DAX-B02E2D?style=flat-square&logo=powerbi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-184F95?style=flat-square&logo=docker&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-monitoring-B02E2D?style=flat-square&logo=grafana&logoColor=white)

---

<!--LIVE:start-->
### What moved recently

| | | |
|---|---|---|
| **[nhmTri](https://github.com/nhmTri/nhmTri)** | chore: refresh the live profile block | `1d ago` |
| **[nhmTri.github.io](https://github.com/nhmTri/nhmTri.github.io)** | feat: publish the portfolio, animated recognition section and all | `1d ago` |
| **[rfm-segmentation-sql](https://github.com/nhmTri/rfm-segmentation-sql)** | feat: Codespaces, a re-runnable sample, the animated matrix and the … | `1d ago` |
| **[voucher-abuse-detection](https://github.com/nhmTri/voucher-abuse-detection)** | feat: Codespaces, a re-runnable sample, the animated diagram and the… | `1d ago` |
| **[FPT_processing_bigdata](https://github.com/nhmTri/FPT_processing_bigdata)** | feat: CI with a data contract and a leak guard, real requirements.txt | `1d ago` |

### Every repository below runs its own tests

[![voucher-abuse-detection](https://img.shields.io/badge/voucher--abuse--detection-passing-1F7A5A?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/nhmTri/voucher-abuse-detection/actions) [![rfm-segmentation-sql](https://img.shields.io/badge/rfm--segmentation--sql-passing-1F7A5A?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/nhmTri/rfm-segmentation-sql/actions) [![Job_realtime](https://img.shields.io/badge/Job_realtime-passing-1F7A5A?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/nhmTri/Job_realtime/actions) [![Brazilian_E_Commerce](https://img.shields.io/badge/Brazilian_E_Commerce-passing-1F7A5A?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/nhmTri/Brazilian_E_Commerce/actions)

<img src="assets/activity.svg" alt="Commits across public repositories over the last twelve weeks" width="100%">

<img src="assets/stack.svg" alt="Language split across public repositories" width="100%">

<sub>Regenerated from the GitHub API every morning · last run 05 Oct 2026, 07:08 UTC</sub>
<!--LIVE:end-->

---

### Two of these you can actually play with

Not a screenshot — a page where you move the thresholds and watch the answer change.

| | |
|---|---|
| **[Voucher abuse detection](https://nhmtri.github.io/voucher-abuse-detection/)** | Nine abuse pairs are planted in the data. Move the four rule thresholds and the page scores you: how many rings caught, how many ordinary customers swept in with them. |
| **[RFM segmentation](https://nhmtri.github.io/rfm-segmentation-sql/)** | Drag the cut-offs; the grid recolours, the revenue split moves, and the SQL rewrites itself underneath. |

Both also open in **GitHub Codespaces** with PostgreSQL 16 running and the sample loaded — one
button, no install, `make test` and you see the rule fire.

### Selected work

| Project | What it does | Result |
|---|---|---|
| [voucher-abuse-detection](https://github.com/nhmTri/voucher-abuse-detection) | Pair-level network rules on campaign transactions | Closed ring of **3 buyers, 3 sellers** on 1-VND orders, at **100% precision** against the planted truth |
| [rfm-segmentation-sql](https://github.com/nhmTri/rfm-segmentation-sql) | RFM scoring with CTEs and window functions, every cut-off a parameter | Champions spend **39% more** at the same frequency |
| [Job_realtime](https://github.com/nhmTri/Job_realtime) | Kafka → Spark Streaming → Cassandra → MySQL, with CDC and Grafana | 2 live sources, postings visible in minutes, fully replayable |
| [Brazilian_E_Commerce](https://github.com/nhmTri/Brazilian_E_Commerce) | Medallion pipeline on Olist: DQ gate, SCD2 dimensions, streaming fact layer | Late delivery predicts a bad review at **r = 0.68** |
| [FPT_processing_bigdata](https://github.com/nhmTri/FPT_processing_bigdata) | Staged Spark batch over nested JSON | 10M rows → 1M OLAP rows in **under 250s** |

Full case studies, with the analysis and the reasoning: **[portfolio](https://portfolionhmtri.netlify.app)**

---

No client data, client names or client figures appear in any repository here. Every dataset used is public, synthetic, or my own.

📫 nguyenhoangminhtri1410@gmail.com
