import os
import sys
import random
import json
from datetime import datetime, timedelta, timezone

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.concept_edge import ConceptEdge
from app.models.scheduling import SchedulingData
from app.models.review_log import ReviewLog
from app.models.propagation_log import PropagationLog
from app.algorithms import sm2, fsrs, multi_fsrs
from app.algorithms.knowledge_graph import GraphManager

db = SessionLocal()

def seed_data():
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        print("User 1 not found!")
        return

    print("Cleaning up old data for User 1...")
    db.query(PropagationLog).filter(PropagationLog.user_id == 1).delete()
    db.query(ReviewLog).filter(ReviewLog.user_id == 1).delete()
    db.query(ConceptEdge).filter(ConceptEdge.user_id == 1).delete()
    db.query(SchedulingData).filter(SchedulingData.user_id == 1).delete()
    db.query(Concept).filter(Concept.user_id == 1).delete()
    db.query(Subject).filter(Subject.user_id == 1).delete()
    db.commit()

    start_date = datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2026, 6, 29, 20, 0, 0, tzinfo=timezone.utc)

    # 1. Create Subjects
    subj_dsa = Subject(user_id=1, name="DSA in C++", description="Data Structures and Algorithms implemented in modern C++", created_at=start_date)
    subj_os = Subject(user_id=1, name="Operating Systems", description="Core OS concepts, concurrency, and memory", created_at=start_date + timedelta(days=2))
    subj_sys = Subject(user_id=1, name="System Design", description="Distributed systems and architecture patterns", created_at=start_date + timedelta(days=5))
    
    db.add_all([subj_dsa, subj_os, subj_sys])
    db.commit()

    # 2. Define Concepts (Hierarchical for Graph)
    concept_defs = [
        # DSA
        (subj_dsa, "Pointers & References", '{"front": "Explain pointers vs references", "back": "Pointers hold memory addresses and can be null/reassigned.\\n\\n```cpp\\nint x = 5;\\nint* ptr = &x;\\nint& ref = x;\\n```"}', None),
        (subj_dsa, "Dynamic Arrays (std::vector)", '{"front": "How does std::vector grow?", "back": "It allocates a new contiguous block of double the capacity and moves elements.\\n\\n```cpp\\nstd::vector<int> v;\\nv.push_back(10);\\n```"}', "Pointers & References"),
        (subj_dsa, "Linked List Node", '{"front": "Implement a Singly Linked List Node", "back": "Requires a value and a pointer to the next node.\\n\\n```cpp\\nstruct Node {\\n    int data;\\n    Node* next;\\n    Node(int d) : data(d), next(nullptr) {}\\n};\\n```"}', "Pointers & References"),
        (subj_dsa, "Reverse Linked List", '{"front": "Write code to reverse a Linked List", "back": "Iterate while maintaining prev, curr, and next pointers.\\n\\n```cpp\\nNode* reverse(Node* head) {\\n    Node *prev = nullptr, *curr = head;\\n    while(curr) {\\n        Node* next = curr->next;\\n        curr->next = prev;\\n        prev = curr;\\n        curr = next;\\n    }\\n    return prev;\\n}\\n```"}', "Linked List Node"),
        (subj_dsa, "Cycle Detection (Floyd)", '{"front": "How to detect a cycle in a linked list?", "back": "Use fast and slow pointers.\\n\\n```cpp\\nbool hasCycle(Node* head) {\\n    Node *slow = head, *fast = head;\\n    while(fast && fast->next) {\\n        slow = slow->next;\\n        fast = fast->next->next;\\n        if(slow == fast) return true;\\n    }\\n    return false;\\n}\\n```"}', "Linked List Node"),
        (subj_dsa, "Binary Tree Node", '{"front": "Define a Binary Tree Node", "back": "```cpp\\nstruct TreeNode {\\n    int val;\\n    TreeNode* left;\\n    TreeNode* right;\\n};\\n```"}', "Pointers & References"),
        (subj_dsa, "DFS Traversal", '{"front": "Write a recursive DFS (Inorder)", "back": "```cpp\\nvoid inorder(TreeNode* root) {\\n    if(!root) return;\\n    inorder(root->left);\\n    cout << root->val;\\n    inorder(root->right);\\n}\\n```"}', "Binary Tree Node"),
        (subj_dsa, "BFS Traversal", '{"front": "Write Level Order Traversal (BFS)", "back": "Use a std::queue.\\n\\n```cpp\\nvoid bfs(TreeNode* root) {\\n    queue<TreeNode*> q;\\n    q.push(root);\\n    while(!q.empty()) {\\n        TreeNode* curr = q.front(); q.pop();\\n        if(curr->left) q.push(curr->left);\\n        if(curr->right) q.push(curr->right);\\n    }\\n}\\n```"}', "Binary Tree Node"),
        (subj_dsa, "Binary Search", '{"front": "Implement iterative Binary Search", "back": "```cpp\\nint search(vector<int>& nums, int target) {\\n    int l = 0, r = nums.size() - 1;\\n    while(l <= r) {\\n        int m = l + (r - l) / 2;\\n        if(nums[m] == target) return m;\\n        if(nums[m] < target) l = m + 1;\\n        else r = m - 1;\\n    }\\n    return -1;\\n}\\n```"}', "Dynamic Arrays (std::vector)"),
        (subj_dsa, "Hash Map (std::unordered_map)", '{"front": "Time complexity of unordered_map insertions?", "back": "Average O(1), Worst case O(N) due to collisions.\\n\\n```cpp\\nunordered_map<int, int> mp;\\nmp[5] = 10;\\n```"}', "Dynamic Arrays (std::vector)"),
        (subj_dsa, "Two Sum", '{"front": "Solve Two Sum using a Hash Map", "back": "```cpp\\nvector<int> twoSum(vector<int>& nums, int target) {\\n    unordered_map<int, int> mp;\\n    for(int i=0; i<nums.size(); i++) {\\n        if(mp.count(target - nums[i])) return {mp[target-nums[i]], i};\\n        mp[nums[i]] = i;\\n    }\\n    return {};\\n}\\n```"}', "Hash Map (std::unordered_map)"),
    ]

    # Generate more DSA concepts
    algorithms = ["Dijkstra", "Bellman-Ford", "Kruskal", "Prim", "Topological Sort", "KMP Algorithm", "Rabin-Karp"]
    dp_problems = ["Fibonacci", "Knapsack 0/1", "Longest Common Subsequence", "Coin Change", "Edit Distance"]
    
    for i, algo in enumerate(algorithms):
        parents = ["BFS Traversal", "DFS Traversal", "Binary Search", "Pointers & References", "Dynamic Arrays (std::vector)"]
        concept_defs.append((subj_dsa, algo, f'{{"front": "Implement {algo}", "back": "```cpp\\n// {algo} implementation\\n```"}}', parents[i % 5]))
    
    for i, dp in enumerate(dp_problems):
        parents = ["Dynamic Arrays (std::vector)", "Hash Map (std::unordered_map)", "Two Sum", "Linked List Node", "Pointers & References"]
        concept_defs.append((subj_dsa, f"DP: {dp}", f'{{"front": "Solve {dp}", "back": "```cpp\\n// {dp} DP implementation\\n```"}}', parents[i % 5]))

    # Generate many generic DSA problems to reach ~50 DSA total
    prev_concept = "Hash Map (std::unordered_map)"
    for i in range(1, 28):
        concept_defs.append((subj_dsa, f"Leetcode Pattern #{i}", '{"front": "Problem Pattern", "back": "```cpp\\n// Approach and Code\\n```"}', prev_concept))
        prev_concept = f"Leetcode Pattern #{i}"

    # OS Concepts
    os_defs = [
        (subj_os, "Process vs Thread", '{"front": "Process vs Thread", "back": "Processes have separate memory spaces. Threads share memory within a process."}', None),
        (subj_os, "Mutex", '{"front": "What is a Mutex?", "back": "Mutual exclusion lock to prevent race conditions."}', "Process vs Thread"),
        (subj_os, "Deadlock Conditions", '{"front": "4 Deadlock Conditions", "back": "1. Mutual Exclusion\\n2. Hold and Wait\\n3. No Preemption\\n4. Circular Wait"}', "Mutex"),
        (subj_os, "Virtual Memory", '{"front": "Virtual Memory", "back": "Abstracts physical memory, giving each process a contiguous virtual address space using paging."}', "Process vs Thread"),
        (subj_os, "Page Fault", '{"front": "Page Fault", "back": "Occurs when a program accesses a page mapped in virtual memory but not loaded in physical RAM."}', "Virtual Memory"),
    ]
    concept_defs.extend(os_defs)

    # System Design Concepts
    sys_defs = [
        (subj_sys, "CAP Theorem", '{"front": "CAP Theorem", "back": "Consistency, Availability, Partition Tolerance. Pick 2."}', None),
        (subj_sys, "Load Balancing", '{"front": "Load Balancing", "back": "Distributes incoming network traffic across multiple servers."}', "CAP Theorem"),
        (subj_sys, "Consistent Hashing", '{"front": "Consistent Hashing", "back": "Used to distribute data across nodes minimizing reorganization when nodes are added/removed."}', "Load Balancing"),
        (subj_sys, "Database Sharding", '{"front": "Database Sharding", "back": "Horizontal partitioning of data across multiple DB instances."}', "Consistent Hashing"),
        (subj_sys, "Redis Caching", '{"front": "Redis Caching", "back": "In-memory key-value store used to reduce DB load."}', "CAP Theorem"),
    ]
    concept_defs.extend(sys_defs)

    print(f"Generating {len(concept_defs)} concepts...")
    
    concept_map = {} 
    algs = ["sm2", "fsrs", "multi_fsrs"]

    creation_cursor = start_date
    for idx, (subject, title, content, parent_title) in enumerate(concept_defs):
        if idx % 5 == 0 and creation_cursor < end_date - timedelta(days=5):
            creation_cursor += timedelta(days=1)
            
        c = Concept(
            user_id=1,
            subject_id=subject.id,
            title=title,
            content=content,
            difficulty="medium",
            created_at=creation_cursor
        )
        db.add(c)
        db.flush()
        concept_map[title] = c
        
        if parent_title and parent_title in concept_map:
            c.parent_concept_id = concept_map[parent_title].id
            GraphManager.add_edge(db, 1, c.parent_concept_id, c.id, w_expert=0.7)
            
        sched = SchedulingData(
            user_id=1,
            concept_id=c.id,
            algorithm=random.choice(algs),
            next_review_date=creation_cursor,
            created_at=creation_cursor,
            updated_at=creation_cursor
        )
        db.add(sched)

    db.commit()

    print("Simulating study sessions from June 3 to June 29...")
    current_sim_date = start_date
    total_reviews = 0

    while current_sim_date <= end_date:
        due_schedules = db.query(SchedulingData).join(Concept).filter(
            SchedulingData.user_id == 1,
            SchedulingData.next_review_date <= current_sim_date,
            Concept.created_at <= current_sim_date
        ).all()
        
        if due_schedules:
            cards_to_review = due_schedules[:random.randint(15, 30)]
            
            for sched in cards_to_review:
                r = random.random()
                if sched.stability < 1.0:
                    rating = random.choices([1, 2, 3, 4], weights=[0.2, 0.3, 0.4, 0.1])[0]
                elif sched.stability < 5.0:
                    rating = random.choices([1, 2, 3, 4], weights=[0.05, 0.15, 0.6, 0.2])[0]
                else:
                    rating = random.choices([2, 3, 4], weights=[0.05, 0.5, 0.45])[0]

                concept = db.query(Concept).filter(Concept.id == sched.concept_id).first()
                if sched.algorithm == "sm2":
                    updated = sm2.calculate(sched, rating)
                elif sched.algorithm == "fsrs":
                    updated = fsrs.calculate(sched, rating)
                else:
                    # Make sure we don't use real datetime.now() inside multi_fsrs if it logs.
                    # Actually multi_fsrs uses datetime.now(timezone.utc) in propagation.py. 
                    # We can monkeypatch datetime just for the simulation to ensure historical timestamps!
                    updated = multi_fsrs.calculate(sched, rating, concept=concept, db=db)
                
                sched.stability = updated["stability"]
                sched.difficulty_fsrs = updated.get("difficulty_fsrs", sched.difficulty_fsrs)
                sched.interval_days = updated["interval_days"]
                sched.retrievability = updated["retrievability"]
                
                sched.next_review_date = current_sim_date + timedelta(days=sched.interval_days)
                sched.updated_at = current_sim_date

                log = ReviewLog(
                    user_id=1,
                    concept_id=sched.concept_id,
                    algorithm_used=sched.algorithm,
                    quality_score=rating,
                    reviewed_at=current_sim_date,
                    response_time_sec=random.randint(5, 45), 
                    was_correct=(rating > 1),
                    retention_at_review=sched.retrievability,
                    post_review_stability=sched.stability,
                    post_review_interval=sched.interval_days
                )
                db.add(log)
                total_reviews += 1
                
        db.commit()
        # For historical propagation logs, we must update their created_at which was just inserted by multi_fsrs
        if total_reviews > 0:
            from sqlalchemy import text
            db.execute(text(
                f"UPDATE propagation_logs SET created_at = '{current_sim_date.isoformat()}' "
                f"WHERE created_at > '{end_date.isoformat()}'"
            ))
            db.commit()

        current_sim_date += timedelta(days=1)

    print(f"Simulation complete! Inserted {len(concept_defs)} concepts and generated {total_reviews} historical review logs.")

if __name__ == "__main__":
    seed_data()
