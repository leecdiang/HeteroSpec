# v0.7 delivery manifest

Starting main: `bab0e44c74f7fa59d2ea42faf4dcf4c51a78e674`.
Branch: `paper/mlsys2027-direct-id-integration-v0.7`.
Artifact-freeze checkpoint: `1ea5c6e09d01c3219631f183fc1934db84955a66`.
Final containing commit is the Draft PR head; this document avoids a self-referential commit hash.

Exact base-to-delivery inventory: **77 files**, all under `paper/mlsys2027/`.
A = added; M = modified. File hashes cover delivered bytes, except this manifest itself.
No deleted files, changed historical evidence, new inference, or retrospective timing certification.

## Delivered artifacts

| Artifact | SHA-256 | Pages or bundle |
|---|---|---|
| manuscript-v0.7.pdf | `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670` | 10 body + 1 references |
| appendix-v0.7.pdf | `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f` | 5 appendix |
| hardware-only-v0.7.pdf | `785680bc537d56271fa5e5adebb1e4b2151f6211f00c23199bdce6db61816030` | 9 body + 1 references |
| overleaf-direct-id-integration-v0.7.zip | `68d3a833a3d1dc1ed48d9560b2b4dadb226c15b051cf0753f0ca307e3ca0dedb` | 39 files; clean main/appendix builds match |

## Completed verification

Historical numerical 228; protected narrative 260 and historical macros 57; runtime 136 and sourced macros 29; M4 primary payload hashes 62; independent secondary checks 638; unchanged tests 7; submission checks 41; direct-ID integration 2459 and independent Figure 3 checks 67: all PASS.
Both content-addressed qualification archives independently replay 270 executions and 180 comparisons each. Omitted external weights/binaries have validated recorded identities, not newly rehashed local bytes.
All 26 rendered pages and actual Figure 3 color/grayscale at 96/200 dpi PASS. Figure 3 is 6.75 x 2.12 in, with separate historical physical opportunity and prospective qualification panels.
Official style unchanged; anonymous PDFs; full author lists for all 15 references; embedded fonts; no substitutions, unresolved citations/references or overfull boxes.
Seven independent model reviews plus meta/mock/delta complete. Mock Weak Reject, moderate confidence 3/5; remaining objection is limited transferable explanatory/predictive reach. Scientifically coherent and ready for author review.

## Exact added/changed files

| Status | Repository-relative file | SHA-256 |
|---|---|---|
| M | `paper/mlsys2027/MANUSCRIPT_STATUS.md` | `c398e036c2bd33e32b0952c935ed162ea348b5823ae2632f4480dde80988e468` |
| M | `paper/mlsys2027/README.md` | `51bba56fe2a86908a407405462f8f38153984be036c6f3a995984c28ea332a9f` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_B570_OFFLINE_V07.json` | `6f7e2c1dc18b86fe60eccb959c04d396d51531b39d209e32c0e4549050bb1bfa` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_BUILD_QA_V07.json` | `64293a315e1a6a777e4b8d54286d0df2c9b7344f9946908dabba17fde9840b99` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_DELIVERY_MANIFEST_V07.md` | `self; omitted` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_INTEGRATION_AUDIT_V07.md` | `2265083e96013a3cc8a1dc05925e7bc9690aebae2106a88f98c401f37bab43d1` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_INTEGRATION_QA_V07.json` | `28d2a7038a7b17fb37a8e5cbaf03453d42540a295c980513d601495fc996c1c2` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_M4_SECONDARY_REPLAY_V07.json` | `22ba6d5f8d4fd671f8e091a1d071091e502461564b746629060ca3f4a50de241` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_M4_TEST_QA_V07.json` | `f0afb886cbe9cb7eb3096133a40f566d03b29ff59c4c60fae1c8bb52108890c6` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_QUALIFICATION_SCOPE_V07.md` | `90bcc3538862ea855a5635dd035f400a6fb31f9c52a4c7f61bc8d4309e2c91f1` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_RENDERED_PAGES_V07.json` | `a5aa87b72ec237a1a0b39053bae8c84093077245dbf0534d973f7388d2a9c1eb` |
| A | `paper/mlsys2027/evidence/DIRECT_ID_RTX_OFFLINE_V07.json` | `32bb2af0c77bcd7264aed0e462d0fcf3ec6e0721d332b6b50d74060d945beb01` |
| A | `paper/mlsys2027/evidence/NARRATIVE_FIGURE_V07_QA.json` | `5b5f962f1632fee4098e09ec70ef0208b1589f1b4b6fe71faa22630ca9ba2592` |
| A | `paper/mlsys2027/evidence/NARRATIVE_PDF_V07_QA.json` | `d6a52934f29d64a1ad0b686bd31e2b318ae040ef69cdb744d2650afc47b1e55c` |
| A | `paper/mlsys2027/evidence/NARRATIVE_V07_QA.json` | `faefe7fba155dc46f71cb4b26d7d36f67cc6b6453fa688cc2a2f4372e7b765f3` |
| A | `paper/mlsys2027/evidence/NUMERICAL_QA_V07.json` | `54fb9b414eee3eb45e122ffc38589ccd3a1a1f9c499db5a20f23022a5d79420d` |
| A | `paper/mlsys2027/evidence/RUNTIME_QA_V07.json` | `c9e8b06ffb893f23256f80421778a482f8ea21e2a9ac40b0347196e6320331f0` |
| A | `paper/mlsys2027/evidence/SUBMISSION_QA_V07.json` | `c00223188bd15a1a6a5b32ff1ea87bc9732031abf4636537cac97debaab87cbf` |
| M | `paper/mlsys2027/manuscript/Makefile` | `3dafd88ec585ce8b3927fbfdf15b2e7cb91bd9f20f6b80f4789e99cb777d4880` |
| M | `paper/mlsys2027/manuscript/README.md` | `1e0e2259b2195e2d38028a6c60f9bfb6c480bc00868cf7f45f3324b3c3664699` |
| M | `paper/mlsys2027/manuscript/appendix.tex` | `7ac6688fa2c57a6068924a6dd03f31ae83612db1a2dfd37b227d4f911fd5f8fb` |
| M | `paper/mlsys2027/manuscript/figures/03_verification.tex` | `8aa9737f50cbea2639e306f60ebad8d5b730dba0f99e559bcb45747ec815d6dd` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/README.md` | `98f91cf26fb03668bc1f60bc6565f8f598022b93b2265e88e3e5706048e86b57` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/pdf/verification.pdf` | `75a4cc30d24bc07e6c57c8730f42185319811a07cef84f1de00bbd4914fd5939` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/plot.py` | `d8cc44a0e74368bcdbe92864b8bb4c14f7c042ac1758994ec428c58517cd20fc` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/validation.json` | `3b4deaa751539391ad5698ec13c0a66513743c9c551ef524e6b0edfe043857eb` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification.json` | `5232b3bf7a090246e5061dd5e5840bc1c8bf7803d389d8a27425fd66afac5e90` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_color_200.png` | `ea7a04c771846c4169ae37b669543547bb68d37bd8e94d9252b8d29337266ab6` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_color_96.png` | `4e292e0fba2a96d774c8ec31b8e6b9d37b0666b57879d548e3ed21377f69f009` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_grayscale_200.png` | `4fcb3dadb63d29865d1a090642b6aad3fecc1524df720399fb3a31e1b1e4524a` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_grayscale_96.png` | `da352e931888a8a26e57bf51cb9bf30c3e1d99045df531b83c6420f150146c09` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_pdf_color_200.png` | `734cb7857522c47fd81e49a0a3529b33c7569731c30026a38e1dc3053acca93c` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_pdf_color_96.png` | `2ff813b79bf8f23168174ab6968b944ed8ed415b8df57bf940e2622134af0b81` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_pdf_grayscale_200.png` | `34c4aea94f9af37587244741884bf301e5c02a2219f371714359dc27ead14927` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/qa/verification_pdf_grayscale_96.png` | `1f5074e97d78ecf051b328b21237cab8a36a694008a253ce801b4dd20b0d97aa` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/svg/verification.svg` | `62110e9f4b98e5725ed361450aa3f46af3d343896b6bebca7033e17e2914675a` |
| A | `paper/mlsys2027/manuscript/figures/presentation_v07/validate.py` | `bca3d0cd605641476264a760859e609f4ffe9cf01d3d587d1ea7c27f0a6a2b72` |
| M | `paper/mlsys2027/manuscript/main.tex` | `047dde09cc20832fd5988f249f17af21c2dd0a4a2e041777c7555d21db9eadcd` |
| A | `paper/mlsys2027/manuscript/output/appendix-v0.7.pdf` | `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f` |
| A | `paper/mlsys2027/manuscript/output/hardware-only-v0.7.pdf` | `785680bc537d56271fa5e5adebb1e4b2151f6211f00c23199bdce6db61816030` |
| A | `paper/mlsys2027/manuscript/output/manuscript-v0.7.pdf` | `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670` |
| A | `paper/mlsys2027/manuscript/output/overleaf-direct-id-integration-v0.7.zip` | `68d3a833a3d1dc1ed48d9560b2b4dadb226c15b051cf0753f0ca307e3ca0dedb` |
| A | `paper/mlsys2027/manuscript/scripts/build_v07.py` | `14570f44f257e38bd2ed875d08e84c576ca666d45af9f4488cad64a2acf363b1` |
| A | `paper/mlsys2027/manuscript/scripts/direct_id_values.py` | `63888ce178db381261507711ead56b9a082ebebd8efa0aa68c90bc2a021cc3cd` |
| M | `paper/mlsys2027/manuscript/scripts/package_overleaf.py` | `a38c0aebce5821dc02b1c1d9a2ef436a6ad27fa18591d6bb12c0fd3c4df02afc` |
| M | `paper/mlsys2027/manuscript/scripts/qa_pdf.py` | `4ba1b833af9936ba5041251bf9b5fef4797622e6b1fd7fccbf164829963704b0` |
| A | `paper/mlsys2027/manuscript/scripts/render_v07.py` | `b48afb5a03f00ce3dd4eda09da6f9f9255080f6cc640faec73d255e1c2790740` |
| A | `paper/mlsys2027/manuscript/scripts/replay_direct_id_archives.py` | `6111d8a0840f94a03d9694196c79460fdf49905e973ad1dc148cead5a8092bcd` |
| M | `paper/mlsys2027/manuscript/scripts/run_historical_validation.py` | `c1a28876877d19bf8b80632c08f2e6bb5d50dbb2cc5f8d8272a3f655e9dccc40` |
| A | `paper/mlsys2027/manuscript/scripts/test_existing_v07.py` | `05b77301fca45bacb8c0130a2e042f0da8507b12a644ee362b935bd87e100281` |
| A | `paper/mlsys2027/manuscript/scripts/validate_direct_id.py` | `728ae67c909dd9d2fb2c370fb0ab057881afb397393ba6d39e45dd83dc481e86` |
| M | `paper/mlsys2027/manuscript/scripts/validate_figures.py` | `b2142a90fa040b3d53a8fb869a96db3d279d2bd1f55d085ccde10063e691ba59` |
| M | `paper/mlsys2027/manuscript/scripts/validate_narrative.py` | `2afb5282b73863347a6d0c1ed0cf6b6ea713cc164e2c814a3846e43572b3099c` |
| M | `paper/mlsys2027/manuscript/scripts/validate_runtime.py` | `1087bcb380d58082673bd702a52962a9182f2cc956caebbb594a9c83e98c47f9` |
| M | `paper/mlsys2027/manuscript/scripts/validate_submission.py` | `badadcf90dbb594221b0e091b4d8a278fc149f409b0be9f76cacd7082f60d24b` |
| M | `paper/mlsys2027/manuscript/sections/01_introduction.tex` | `c379e5a04f54b5140b243409d064d36a78c157df8688b21aebfb323d19e886b6` |
| M | `paper/mlsys2027/manuscript/sections/02_framework.tex` | `a7f8d2a73d3d954ca929805d25629285f89520a3f34f5258b1270230a732e65a` |
| M | `paper/mlsys2027/manuscript/sections/03_methodology.tex` | `336c22e46079ee3a9ae5de39e8309d99f20919382dc2b287d0bf87636e5bb692` |
| M | `paper/mlsys2027/manuscript/sections/04_outcomes.tex` | `adc7a9357c4dee6952e33a6a7c9fa4921d40941a27592df23bf26d8b6bebf8f5` |
| M | `paper/mlsys2027/manuscript/sections/05_diagnoses.tex` | `47f28c426c52aecbbd36273418b8ba8ea406787a4e9f75b1ed92dc28018dd16f` |
| M | `paper/mlsys2027/manuscript/sections/06_synthesis.tex` | `6616213420f02854cdcc9a69a806d94d786f799069a8e8d1a7908a0a3a21b7ab` |
| M | `paper/mlsys2027/manuscript/sections/08_related_work.tex` | `408067aa396270e80b3a9da86c7105ebbfc74ab7628cedbf0817eac24a587a92` |
| M | `paper/mlsys2027/manuscript/sections/09_limitations.tex` | `cd472395f1a0f767017887e773d131e6fb6223532b8d888fcac49bb292dfc8cd` |
| M | `paper/mlsys2027/manuscript/sections/10_conclusion.tex` | `27748f512206be18352cca17d512a1c5e1a16e0a7af855bdd119ac9ee6223316` |
| A | `paper/mlsys2027/manuscript/tables/08_direct_id.tex` | `ac6fe886b6d941f9f72adce1a7f1f23d2a76c83d295e20948a32010952443f31` |
| A | `paper/mlsys2027/manuscript/tables/direct_id_values.tex` | `237155dc4a7c037a0822ce78cb6780cef8eb33486dba7b9e7b2f9ee5084961c4` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_ADVERSARIAL.md` | `c1dc5be7bc7b3dd36be2634c76d2a999397b5003501b6f45b7dbb6600c035bda` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_NOVELTY.md` | `449d53ab8b6d099fc50da904f5fd59526ebb7de6f18976be3cfe9aa8d687b5b9` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_RIGOR.md` | `7be892a8142c21101ded37536dd8086b61ffbfc03bd052b1dae3d2a450860bac` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_SYSTEMS.md` | `c54c6d82e2f0ac20cbf0aa09aa4857b0b52907cc86d31e48067c011e3338a4d5` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_VISUAL.md` | `e74d80be1fae480bc127f713daa10a0f88b5777912ea8bbef510fd856506f019` |
| A | `paper/mlsys2027/reviews/submission_v07/FINAL_WRITING.md` | `72390c66430dcdd1e8622894498a073c5e8620015fbdb092deee9f015a8fee1c` |
| A | `paper/mlsys2027/reviews/submission_v07/FUTURE_WORK_RECOMMENDATIONS.md` | `233a07bf5e5d1e6f04e03f46e1c313830190da2a10eb4cbf3bb0db62d6c1f37b` |
| A | `paper/mlsys2027/reviews/submission_v07/META_REVIEW.md` | `e63d5db2ca739510cc187041b88cd67fe661a2fcdfe63f2a0ed2dc39daec855e` |
| A | `paper/mlsys2027/reviews/submission_v07/MOCK_DECISION.md` | `8e2da932fe6a9b72ec2f7c19ed7987a5586998c1ae8c2679ba2ee86ee20c62ea` |
| A | `paper/mlsys2027/reviews/submission_v07/REVIEW_CHAMPION.md` | `c327ecb0e950ac46214d9d95c67eb89cbf514a7c5fbfe390171b698c5b1557bf` |
| A | `paper/mlsys2027/reviews/submission_v07/REVIEW_DELTA_V05_TO_V07.md` | `504c5fa74ad824f00f222434eeb2eacedf7a850290c04348acf5bb47b5a2319f` |
