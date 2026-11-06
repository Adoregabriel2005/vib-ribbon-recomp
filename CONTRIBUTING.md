# Como testar e contribuir

Leia README.md e docs/STATUS.md. Use seu próprio dump europeu SCES-02873.
Inclua no relato: commit, Windows, CPU/GPU, renderizador, controles, passos para
reproduzir e resultado esperado/observado. Informe fonte musical e modo manual/Demo.

Não envie ROMs, BIOS, músicas ou saves pessoais. Revise dados pessoais dos logs
antes de compartilhar somente o trecho necessário. Relatórios ficam locais.

Descreva o problema e os testes no PR. Preserve OpenBIOS, REFERENCE/LLE e o áudio
original. Não edite C gerado para forçar progressão nem relaxe guards. O intérprete
é fallback: geração de código não equivale a cobertura medida.

Execute os testes Python e tools/check_repository.py. Mudanças em submódulos
precisam de patch em patches/ para que outra cópia reproduza a alteração.
Não envie builds, dados do disco ou caches em commits.
