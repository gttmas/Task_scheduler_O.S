Simulador de Escalonamento de Tempo Real

Este projeto consiste em um ambiente simulador de sistemas operacionais voltado para o estudo, visualização e análise de algoritmos de escalonamento em tempo real multitarefa. Desenvolvido com uma arquitetura modular que separa a lógica do sistema da camada gráfica, o aplicativo permite carregar arquivos de configuração, ajustar parâmetros de processamento em tempo de execução, injetar ou editar tarefas dinamicamente e acompanhar a execução detalhada por meio de monitores e diagramas de linha do tempo.

Tecnologias Utilizadas

A aplicação foi inteiramente desenvolvida em Python. A interface gráfica utiliza o framework PySide6, aproveitando recursos avançados do Qt como gerenciamento de layouts, controle de temporizadores globais, sinalização por eventos e janelas empilhadas em memória. Para a renderização do gráfico da linha do tempo, utilizou-se a biblioteca Matplotlib integrada ao Qt através do componente de tela do Pyside6, permitindo gerar visualizações escaláveis e exportação gráfica de alta resolução.

Estrutura do Bloco de Controle de Tarefas (TCB)

Cada tarefa gerenciada pelo simulador é representada por uma instância da classe TaskControlBlock. O TCB funciona como a estrutura de dados central onde o sistema operacional armazena todas as características fixas e os estados dinâmicos necessários para tomar decisões de escalonamento.

Dentro do TCB, os parâmetros fixos compreendem o identificador único da tarefa, a cor em formato hexadecimal usada para representação visual, o tempo de ingresso no sistema, a duração total de computação exigida por ciclo, o período de repetição, o prazo relativo e os eventos associados.

As variáveis de estado dinâmico acompanham a situação da tarefa a cada pulso do relógio global. O estado atual pode variar entre Não Iniciada, Pronta, Executando, Suspensa, Concluída ou Cancelada. Além disso, o TCB mantém o registro da CPU que está alocada para a tarefa no momento, o tempo de duração restante para terminar a execução do ciclo atual, a marcação temporal do próximo tempo de liberação e o prazo absoluto, calculado somando o próximo tempo de liberação ao prazo relativo. Para controle de ciclo de vida, a estrutura contabiliza as execuções já finalizadas em relação ao limite total de execuções permitido.

Algoritmos de Escalonamento Implementados

O motor da simulação conta com dois dos mais importantes algoritmos de tempo real, organizados em um registro extensível que permite a ordenação e preempção das tarefas de forma determinística.

Rate Monotonic (RM)

O algoritmo Rate Monotonic aplica uma política de prioridade estática. A prioridade de cada tarefa é definida inversamente ao seu período: quanto menor for o período da tarefa, maior será a sua prioridade de execução. Essa regra baseia-se na frequência da tarefa, garantindo que tarefas que precisam rodar com maior frequência tenham preferência no acesso aos processadores.

Earliest Deadline First (EDF)

O algoritmo Earliest Deadline First utiliza uma política de prioridade dinâmica. A prioridade de cada tarefa é avaliada a cada ciclo com base no seu prazo absoluto. A tarefa que possuir o prazo absoluto mais próximo do tempo atual recebe a maior prioridade. Como o prazo absoluto se renova a cada novo ciclo da tarefa, as prioridades se alteram dinamicamente ao longo do tempo.

Critérios de Desempate

Para evitar comportamentos indeterminados quando duas ou mais tarefas possuem a mesma prioridade primária, o escalonador aplica uma sequência estrita de critérios de desempate ordenados em uma tupla comparativa:

Em primeiro lugar, avalia-se a chave principal do algoritmo selecionado, ou seja, o menor período no RM ou o menor prazo absoluto no EDF. Em segundo lugar, aplica-se a afinidade de execução, concedendo prioridade à tarefa que já se encontra em estado de execução na CPU para minimizar trocas de contexto desnecessárias. Em terceiro lugar, avalia-se o menor prazo absoluto para o RM ou o tempo de ingresso para o EDF. Em quarto lugar, considera-se o tempo de ingresso original da tarefa. Em quinto lugar, compara-se a menor duração total de computação. Por fim, utiliza-se o identificador alfabético único da tarefa para garantir a ordenação.

Detalhamento das Páginas do Sistema

A interface do aplicativo utiliza um gerenciador de janelas empilhadas que mantém quatro páginas carregadas simultaneamente na memória, sincronizando os dados exibidos sempre que o tempo avança.

Página de Configuração do Sistema

A primeira página é dedicada à leitura de arquivos de entrada e ajuste dos parâmetros gerais do sistema operacional. Ela permite selecionar o arquivo de configuração em formato de texto, restaurar os padrões iniciais e definir o algoritmo de escalonamento, a quantidade de CPUs disponíveis e o modo de execução, alternando entre passo a passo e execução completa. A página contém um console de mensagens formatado em código HTML que registra avisos, erros de validação e confirmações de leitura do arquivo, além de uma tabela de resumo contendo as tarefas importadas.

Página de Monitoramento de Processadores

A segunda página fornece uma visualização em tempo real do estado dos processadores do sistema. No topo, são exibidas métricas globais indicando quantas CPUs estão ativas e o tempo total acumulado de ociosidade de todos os núcleos. O corpo central apresenta uma grade com cartões individuais para cada CPU, detalhando o status atual, a tarefa que está em execução naquele núcleo e o tempo ocioso individual. Na parte inferior, é exibida a fila global de tarefas prontas que estão aguardando alocação pelo escalonador.

Página de Gerenciamento de Tarefas (TCB)

A terceira página atua como uma central de controle interativo para inspecionar e modificar as tarefas em tempo de execução. Ela apresenta uma tabela detalhada com nove colunas que mostram todas as informações contidas nos TCBs atualizadas a cada pulso do relógio. Além da visualização, a página possui um painel para injetar novas tarefas durante a simulação com validação de parâmetros, um painel para alterar duração, período, prazo e cor de tarefas já existentes e um painel de modificação manual de estados para forçar situações de teste como suspensão ou cancelamento.

Página do Diagrama de Gantt

A quarta página gera a representação gráfica do histórico da execução ao longo da linha do tempo. Ela utiliza retângulos coloridos para indicar qual tarefa rodou em qual CPU em determinado instante, retângulos brancos para representar o tempo de espera na fila de prontas e marcas hachuradas para tarefas suspensas. Além disso, símbolos coloridos marcam eventos específicos como tempos de liberação, conclusões de ciclos, inícios e fins de suspensão e perdas de prazo relativo.

A Visualização e Exportação do Diagrama de Gantt

O diagrama de Gantt foi construído utilizando os eixos do Matplotlib acoplados a uma área de rolagem do Qt. Essa estrutura foi escolhida porque simulações de tempo real podem se estender por dezenas ou centenas de ciclos de relógio, o que deixaria um gráfico estático espremido e ilegível. Com a área de rolagem, a largura mínima do gráfico se expande proporcionalmente à quantidade de ciclos processados, permitindo navegar horizontalmente mantendo os blocos de tempo com tamanho visível e proporcional.

Em relação ao salvamento do gráfico, a exportação é permitida assim que a simulação atinge o estado final. Em vez de salvar apenas uma captura de tela da janela que poderia sair cortada ou com baixa qualidade, o sistema aciona uma rotina especial que lê o histórico de dados primitivos mantido pelo motor e redesenha toda a linha do tempo em uma nova figura isolada. Essa figura é configurada com fundo claro, ajuste automático de margens e densidade de 300 pontos por polegada, gerando um arquivo de imagem com resolução limpa e profissional, ideal para relatórios e documentos acadêmicos.

Casos de Uso Práticos

Comparação de Desempenho entre Algoritmos

Um estudante de sistemas operacionais deseja analisar como os algoritmos Rate Monotonic e Earliest Deadline First lidam com um conjunto de tarefas com alta taxa de utilização dos processadores. Ele carrega um arquivo de configuração inicial na primeira página, define o modo de execução como completo e seleciona o algoritmo Rate Monotonic. Após finalizar a simulação e verificar as perdas de prazo na página do gráfico, ele reinicia o sistema, seleciona o algoritmo Earliest Deadline First e executa novamente o teste. Comparando as duas imagens exportadas, o estudante consegue identificar visualmente qual algoritmo apresentou menor taxa de perda de prazos para aquele conjunto específico de tarefas.

Injeção Dinâmica de Carga de Trabalho

Um professor deseja demonstrar o conceito de preempção em tempo real para sua turma. Ele inicia a simulação no modo passo a passo com dois processadores ativos e avança alguns ciclos do relógio observando a distribuição regular das tarefas nos cartões de CPU da segunda página. Em seguida, ele navega até a página de gerenciamento de tarefas e utiliza o formulário de injeção para adicionar uma nova tarefa com período curto e prazo urgente. Ao retornar para a tela principal e avançar o próximo ciclo do relógio, a turma observa o escalonador interrompendo imediatamente a execução de uma tarefa que estava na CPU para atribuir o núcleo à nova tarefa injetada.

Teste de Tolerância a Falhas e Modificação Manual

Um desenvolvedor precisa testar como a fila de prontas se reconfigura quando uma tarefa falha ou é interrompida por um evento externo. Durante a execução passo a passo da simulação, ele pausa o tempo no ciclo em que uma tarefa crítica está rodando e utiliza o painel de modificação manual na página de tarefas para alterar o estado dessa tarefa para Suspensa. Ao avançar o tempo, o desenvolvedor acompanha na página de CPUs a liberação imediata do núcleo e observa o escalonador reorganizando a fila global para preencher a vaga com a próxima tarefa de maior prioridade disponível.