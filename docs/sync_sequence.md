# Social Media Sync - Sequence Diagram

The following sequence diagram illustrates the flow of data and control during the social media synchronization process.

```
┌─────────┐      ┌───────┐      ┌─────────────┐      ┌───────┐      ┌───────┐      ┌──────────┐
│  Client │      │  API  │      │Orchestrator │      │Worker │      │Apify  │      │Database  │
└────┬────┘      └───┬───┘      └──────┬──────┘      └───┬───┘      └───┬───┘      └────┬─────┘
     │                │                │                 │              │               │
     │  Sync Request  │                │                 │              │               │
     │────────────────>                │                 │              │               │
     │                │                │                 │              │               │
     │                │  Validate User │                 │              │               │
     │                │───────────────>│                 │              │               │
     │                │                │                 │              │               │
     │                │                │  Queue Tasks    │              │               │
     │                │                │────────────────>│              │               │
     │                │                │                 │              │               │
     │  Task IDs      │                │                 │              │               │
     │<───────────────────────────────────────────────────              │               │
     │                │                │                 │              │               │
     │                │                │                 │              │               │
     │                │                │                 │ Fetch Profile│               │
     │                │                │                 │─────────────>│               │
     │                │                │                 │              │               │
     │                │                │                 │ Profile Data │               │
     │                │                │                 │<─────────────│               │
     │                │                │                 │              │               │
     │                │                │                 │ Fetch Posts  │               │
     │                │                │                 │─────────────>│               │
     │                │                │                 │              │               │
     │                │                │                 │  Posts Data  │               │
     │                │                │                 │<─────────────│               │
     │                │                │                 │              │               │
     │                │                │                 │              │               │
     │                │                │                 │ Transform Data               │
     │                │                │                 │─┐            │               │
     │                │                │                 │ │            │               │
     │                │                │                 │<┘            │               │
     │                │                │                 │              │               │
     │                │                │                 │ Create/Update│SocialPage     │
     │                │                │                 │──────────────────────────────>
     │                │                │                 │              │               │
     │                │                │                 │              │SocialPage ID  │
     │                │                │                 │<──────────────────────────────
     │                │                │                 │              │               │
     │                │                │                 │ Calculate    │               │
     │                │                │                 │ Metrics      │               │
     │                │                │                 │─┐            │               │
     │                │                │                 │ │            │               │
     │                │                │                 │<┘            │               │
     │                │                │                 │              │               │
     │                │                │                 │ Store Metrics│               │
     │                │                │                 │──────────────────────────────>
     │                │                │                 │              │               │
     │                │                │                 │              │   Success     │
     │                │                │                 │<──────────────────────────────
     │                │                │                 │              │               │
     │                │                │                 │ Process Posts│               │
     │                │                │                 │─┐            │               │
     │                │                │                 │ │            │               │
     │                │                │                 │<┘            │               │
     │                │                │                 │              │               │
     │                │                │                 │ Store Posts  │               │
     │                │                │                 │──────────────────────────────>
     │                │                │                 │              │               │
     │                │                │                 │              │   Success     │
     │                │                │                 │<──────────────────────────────
     │                │                │                 │              │               │
     │                │                │                 │              │               │
     │ Check Status   │                │                 │              │               │
     │────────────────>                │                 │              │               │
     │                │  Get Task Status                 │              │               │
     │                │────────────────────────────────> │              │               │
     │                │                │                 │              │               │
     │                │                │      Status     │              │               │
     │                │<───────────────────────────────────              │               │
     │                │                │                 │              │               │
     │ Status Response│                │                 │              │               │
     │<───────────────│                │                 │              │               │
     │                │                │                 │              │               │
┌────┴────┐      ┌───┴───┐      ┌──────┴──────┐      ┌───┴───┐      ┌───┴───┐      ┌────┴─────┐
│  Client │      │  API  │      │Orchestrator │      │Worker │      │Apify  │      │Database  │
└─────────┘      └───────┘      └────────────┘      └───────┘      └───────┘      └──────────┘
```

## Detailed Process Description

### 1. User Initiates Sync

- The client (user or scheduler) sends a sync request to the API.
- The request includes user ID and optionally specific platform(s) to sync.

### 2. Request Validation

- The API validates the request and authenticates the user.
- It checks if the user has valid social media tokens.

### 3. Task Creation

- The Orchestrator creates synchronization tasks for each platform.
- Tasks are added to the Celery queue via Redis.
- Task IDs are returned to the client for status tracking.

### 4. Worker Processing

For each platform (Instagram, Facebook, TikTok):

#### 4.1. External API Communication
- The worker fetches profile data from the Apify API.
- It then fetches recent posts and engagement data.

#### 4.2. Data Transformation
- Raw API data is transformed into our internal data model.
- Calculations are performed for:
  - Engagement rates
  - Growth rates
  - Projected growth
  - Overall social score

#### 4.3. Data Storage
- Profile data is stored in the `SocialPage` table.
- Metrics are stored in various tables:
  - `SocialPageMetric`
  - `SocialPageEngagement`
  - `SocialPageGrowth`
  - `SocialPageReach`
  - `SocialPageScore`
- Posts and comments are stored in:
  - `SocialPagePost`
  - `SocialPagePostComment`

### 5. Status Monitoring

- The client can check the status of sync tasks.
- Tasks can be in one of several states:
  - `PENDING`: Task is waiting to be processed
  - `STARTED`: Task is currently being executed
  - `SUCCESS`: Task completed successfully
  - `FAILURE`: Task failed with an error
  - `REVOKED`: Task was cancelled

### 6. Completion

- Upon successful completion, the data is available for use by the main application.
- The user receives a notification of completion.

## Error Handling

- If a task fails, the error is logged and stored with the task result.
- Depending on the error type, the system may:
  - Retry the task automatically (e.g., for temporary network issues)
  - Mark the task as failed (e.g., for invalid credentials)
  - Notify administrators (e.g., for API quota exceeded)

## Rate Limiting

- The system implements rate limiting to avoid overwhelming the Apify API.
- Default rate: 5 requests per second.
- Batch operations are throttled to stay within limits.