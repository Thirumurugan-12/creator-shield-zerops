from __future__ import annotations

import time

from .services.processing import process_proof
from .services.comparison import compare_incident
from .services.queue import ProofQueue


def main() -> None:
    queue = ProofQueue()
    while True:
        proof_id = queue.dequeue()
        if proof_id:
            process_proof(proof_id)
        else:
            incident_id = queue.dequeue_incident()
            if incident_id:
                compare_incident(incident_id)
            else:
                time.sleep(1)


if __name__ == "__main__":
    main()
