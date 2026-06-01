# Zombie Survival: Alpha Horde

Prototype em Python (Pygame) que demonstra visualmente dois algoritmos de dividir-e-conquistar:

- Closest Pair of Points — usado para unir zumbis próximos em grupos/hordas.
- Mediana das Medianas — usado para escolher o `Alpha` da onda sem ordenar toda a lista.

Como executar:

1. Instale dependências:

```bash
pip install -r requirements.txt
```

2. Rode o jogo:

```bash
python main.py
```

Controles:
- Movimento: `WASD`
- Atirar: clique do mouse

Objetivos pedagógicos:
- Identificar onde o algoritmo Closest Pair acelera a detecção de pares que devem se unir.
- Ver a escolha determinística do `Alpha` com a mediana das medianas, e como isso altera atributos da horda.