# 4. Key Management Pipeline

## Full Key Distillation Pipeline


.. image:: 04-key-management-pipelinea.png
   :alt: 04-key-management-pipeline (slide a)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart TD
    RAW["Raw Key Exchange<br/>Alice: random bits α₁α₂...αₙ<br/>Bob: measured bits β₁β₂...βₙ"]

    subgraph Sifting["Basis Sifting"]
        S1["Compare bases publicly"]
        S2["Keep ~50% where bases match"]
        S3["Discard test bits for QBER"]
    end

    subgraph EC["Error Correction"]
        EC_METHOD{"Method"}

        subgraph Cascade["Cascade Protocol"]
            C1["Divide into blocks (size=4)"]
            C2["Compare block parity"]
            C3{"Parity mismatch?"}
            C4["Binary search for error bit"]
            C5["Flip error bit on Bob's side"]
            C6["Repeat with doubling block sizes"]
            C2 --> C3 -->|yes| C4 --> C5
            C3 -->|no| C6
        end

        subgraph Winnow["Winnow Protocol"]
            W1["Divide into blocks"]
            W2["Hamming syndrome computation"]
            W3["Correct errors via syndrome"]
        end

        subgraph LDPC["Low-Density Parity-Check"]
            L1["Build sparse parity check matrix H"]
            L2["Belief propagation on Tanner graph"]
            L3["Iterate variable→check→variable messages"]
            L4["Check syndrome H·x = 0"]
        end

        EC_METHOD -->|cascade| Cascade
        EC_METHOD -->|winnow| Winnow
        EC_METHOD -->|ldpc| LDPC
    end

    subgraph PA["Privacy Amplification"]
        PA_METHOD{"Method"}

        subgraph UnivHash["Universal Hashing"]
            UH1["Generate random Toeplitz matrix"]
            UH2["Matrix-vector multiply mod 2"]
            UH3["Output: shortened secure key"]
        end

        subgraph Toeplitz["Toeplitz Hashing"]
            T1["Generate random Toeplitz matrix<br/>(diagonal-constant structure)"]
            T2["Efficient FFT-based multiply"]
            T3["Output: shortened secure key"]
        end

        subgraph CryptoHash["Cryptographic Hash"]
            CH1["SHA-3 / SHAKE-256"]
            CH2["Keyed hashing with random salt"]
            CH3["Output: fixed-length digest"]
        end

        subgraph BennettBrassard["Bennett-Brassard 1984"]
            BB1["2-universal hash family"]
            BB2["Output length: n - s - t"]
            BB3["n=corrected, s=security, t=leak"]
        end

        PA_METHOD -->|universal_hashing| UnivHash
        PA_METHOD -->|toeplitz_hashing| Toeplitz
        PA_METHOD -->|cryptographic_hash| CryptoHash
        PA_METHOD -->|bennett_brassard| BennettBrassard
    end

    subgraph Output["Output"]
        O1["Final secure key"]
        O2["Key rate: final / initial"]
        O3["Eve info estimate"]
        O4["Statistics"]
    end

    RAW --> Sifting --> EC --> PA --> Output

    style RAW fill:#bbdefb,stroke:#1565c0
    style Sifting fill:#e1bee7,stroke:#6a1b9a
    style EC fill:#c8e6c9,stroke:#2e7d32
    style PA fill:#d1c4e9,stroke:#4527a0
    style Output fill:#ffe0b2,stroke:#e65100

    style Cascade fill:#e8f5e9,stroke:#1b5e20
    style Winnow fill:#e8f5e9,stroke:#1b5e20
    style LDPC fill:#e8f5e9,stroke:#1b5e20
    style UnivHash fill:#ede7f6,stroke:#311b92
    style Toeplitz fill:#ede7f6,stroke:#311b92
    style CryptoHash fill:#ede7f6,stroke:#311b92
    style BennettBrassard fill:#ede7f6,stroke:#311b92
-->


## Error Correction: Cascade Protocol


.. image:: 04-key-management-pipelineb.png
   :alt: 04-key-management-pipeline (slide b)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
sequenceDiagram
    participant Alice as Alice Key
    participant Channel as Public Channel
    participant Bob as Bob Key

    Note over Alice, Bob: Initial keys of length N

    Alice->>Channel: Block 0 parity = Σ(keys[0:4]) mod 2
    Channel->>Bob: Forward parity

    Bob->>Bob: Compute own parity for block 0

    alt Parities match
        Note over Alice, Bob: No error in this block ✓
    else Parities differ
        Note over Alice, Bob: Error found! Binary search...

        Alice->>Channel: Parity of left half keys[0:2] mod 2
        Bob->>Bob: Compute left half parity
        Bob->>Bob: Compare

        alt Left half matches
            Note over Bob: Error is in right half [2:4]
        else Left half differs
            Note over Bob: Error is in left half [0:2]
        end

        Bob->>Bob: Flip the error bit to match Alice
        Note over Bob: Keys now identical in this block ✓
    end

    Note over Alice, Bob: Repeat for all blocks<br/>Then repeat with doubled block sizes<br/>Typically 4 passes total
-->


## LDPC Belief Propagation


.. image:: 04-key-management-pipelinec.png
   :alt: 04-key-management-pipeline (slide c)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart TD
    subgraph Init["Initialization"]
        I1["Build parity-check matrix H (m × n)"]
        I2["Compute LLR from Alice and Bob keys"]
        I3["Initialize variable-to-check messages = LLR"]
    end

    subgraph Iter["Iteration Loop (max 100)"]
        direction LR

        Check["Check Node Update<br/>tanh(m_cj/2) = ∏ tanh(m_v'j/2)<br/>for all connected v'"]
        Variable["Variable Node Update<br/>m_vi = Σ m_c'i + LLR_i<br/>for all connected c'"]
        Syndrome["Syndrome Check<br/>H · hard_decision = ? 0"]

        Check --> Variable --> Syndrome
    end

    subgraph Decision["Decision"]
        D1{"Syndrome = 0<br/>OR max iterations?"}
        D2["Output corrected keys"]
        D3["FAIL: convergence failed"]
        D1 -->|yes| D2
        D1 -->|no| Iter
    end

    Init --> Iter
    Iter --> Decision
    Syndrome -->|non-zero| D1
-->


## Privacy Amplification: Toeplitz Hashing


.. image:: 04-key-management-pipelined.png
   :alt: 04-key-management-pipeline (slide d)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart TD
    subgraph InputPA["Input"]
        PA_IN["Corrected key k (n bits)"]
        PA_OUT_LEN["Desired output length m < n"]
    end

    subgraph Matrix["Toeplitz Matrix Construction"]
        T11["Generate random seed s (n + m - 1 bits)"]
        T12["Build Toeplitz matrix T (m × n)"]
        T13["T[i,j] = s[i - j + n - 1]<br/>(diagonal-constant structure)"]
    end

    subgraph Multiply["Matrix-Vector Multiply (mod 2)"]
        MUL["T · k mod 2<br/>= m-bit output"]
        MUL_FFT["(Optional) FFT-based<br/>O(n log n) instead of O(nm)"]
    end

    subgraph OutputPA["Output"]
        PA_OUT["Final key k' (m bits)"]
        SEC_PARAM["Security: m ≤ n - s - t<br/>s = 10 (security param)<br/>t = Eve's info estimate"]
    end

    InputPA --> Matrix --> Multiply --> OutputPA
-->


## Key Manager Orchestration


.. image:: 04-key-management-pipelinee.png
   :alt: 04-key-management-pipeline (slide e)
   :width: 100%
   :align: center

<!-- Original mermaid source retained for editor / GitHub viewers.
flowchart TD
    subgraph KM["KeyManager"]
        KM_STATE["state: dict<br/>tracks keys by protocol run"]
        KM_GEN["generate_key(protocol, params)"]
        KM_STORE["store_key(key_id, key)"]
        KM_RETRIEVE["retrieve_key(key_id)"]
        KM_ROTATE["rotate_key(key_id)"]
        KM_DELETE["delete_key(key_id)"]
    end

    subgraph Protocols_KM["QKD Protocols"]
        BB84_KM["BB84"]
        E91_KM["E91"]
        CV_KM["CV-QKD"]
    end

    subgraph Pipeline["Distillation Pipeline"]
        KD_KM["KeyDistillation"]
        EC_KM["ErrorCorrection"]
        PA_KM["PrivacyAmplification"]
    end

    subgraph Storage["Key Storage"]
        MEM["In-memory cache"]
        DB["(Future) Key Store DB"]
    end

    KM -->|runs| Protocols_KM
    KM -->|distills| Pipeline
    KM -->|stores| Storage
    EC_KM --> PA_KM
-->
