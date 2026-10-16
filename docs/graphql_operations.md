# Garmin Connect GraphQL gateway operations

The Garmin Connect web app's home page loads most of its cards through
`POST /graphql-gateway/graphql`. This page lists all of the operations the web
app used in October 2026. Use them with
`Garmin.query_garmin_graphql({"query": "..."})`; the request body is exactly
what the web app sends.

Facts worth knowing:

- Every operation is an **anonymous** `query { ... }` with the arguments
  inlined as literals. There are no named operations, variables, fragments,
  mutations or persisted queries.
- Most root fields end in `Scalar` and return the JSON of the matching REST
  endpoint as an opaque value, so no selection set is given. The few plain
  fields (`pendingActivities`, `cyclingAbility`, `runningEconomy`,
  `healthStatusSummary`, `menstrualCycleDetail`, `calorieSummaryDailyStats`,
  `lifestyleLoggingStats`, `runningToleranceStats`) need the selection sets
  shown below.
- Arguments: dates are `YYYY-MM-DD`; "Connect timestamps" are local wall-clock
  `YYYY-MM-DDTHH:mm:ss.SSS`; `aggregation` is a quoted string except for
  `runningToleranceStats`, where it is an unquoted enum (`daily`).
- The response is `{"data": {"<rootField>": ...}}`.

`${...}` marks a value you substitute.

## Operations

| Root field | Arguments | Used by |
|---|---|---|
| `activitiesScalar` | `displayName, startTimestampLocal, endTimestampLocal, limit` | activities list |
| `activityStatsScalar` | `aggregation, startDate, endDate, metrics:[...], groupByParentActivityType, standardizedUnits[, activityType:[...]]` | activities card |
| `activityTrendsScalar` | `activityType, date` | activity streak card |
| `adhocChallengePendingInviteScalar`, `adhocChallengesScalar`, `badgeChallengesScalar`, `expeditionsChallengesScalar` | none | challenges card |
| `bloodPressureScalar` | `startDate, endDate` | blood pressure card |
| `calorieSummaryDailyStats` | `startDate, endDate, currentDate` | nutrition card |
| `criticalSwimSpeedScalar` | `startDate, endDate` | CSS card |
| `cyclingAbility` | `startDate, endDate` | cycling ability card |
| `dailyEventsScalar` | `date` | timeline |
| `enduranceScoreScalar` | `startDate, endDate, aggregation` | endurance score card |
| `epochChartScalar` | `date, include:[...]` (`"steps"`, `"pushes"`, `"stress"`, `"bodyBattery"`) | steps / body battery / stress cards |
| `functionalThresholdPowerScalar` | `startDate, endDate, sports` | FTP card |
| `golfScorecardScalar` | `startTimestampLocal, endTimestampLocal` | golf card |
| `healthSnapshotScalar` | `startDate, endDate` | health snapshot |
| `healthStatusSummary` | `calendarDate` | health status card |
| `heartRateScalar` | `date` | heart rate card |
| `heartRateVariabilityScalar` | `startDate, endDate` | HRV status card |
| `heatAltitudeAcclimationScalar` | `date` | acclimation card |
| `hillScoreScalar` | `startDate, endDate, aggregation` | hill score card |
| `jetLagScalar` | `date` | jet lag card |
| `latestFitnessAgeScalar` | `asOfDate` | fitness age card |
| `latestWeightScalar` | `asOfDate` | weight card |
| `lifestyleLoggingStats` | `startDate, endDate` | lifestyle logging card |
| `menstrualCycleScalar` | `date` | menstrual cycle card |
| `menstrualCycleDetail` | `date, todayDate` | menstrual cycle details |
| `myDayCardEventsScalar` | `timeZone:"GMT", date` | my day events |
| `pendingActivities` | none | auto-detected activities |
| `personalRecordsScalar` | none | personal records |
| `powerToWeightScalar` | `date, sports` | power-to-weight card |
| `pregnancyScalar` | `date` | pregnancy card |
| `runningEconomy` | `startDate, endDate` | running economy card |
| `runningLactateThresholdScalar` | none | lactate threshold card |
| `runningToleranceStats` | `startDate, endDate, aggregation: daily` | running tolerance card |
| `searchActivitiesScalar` | `start, limit, excludedActivitySubTypes:[...]` | last activity card |
| `sleepScalar` | `date, sleepOnly` | sleep card |
| `sleepSummariesScalar` | `startDate, endDate` | sleep card |
| `spO2AcclimationScalar` | `date` | pulse ox card |
| `trainingLoadBalanceScalar` | `calendarDate, fullHistoryScan:true` | training status card |
| `trainingPlanScalar` | `calendarDate, lang, firstDayOfWeek` | training plan card |
| `trainingReadinessRangeScalar` | `startDate, endDate` | training readiness card |
| `trainingStatusDailyScalar` | `calendarDate` | training status card |
| `trainingStatusWeeklyScalar` | `startDate, endDate, displayName` | training status card |
| `userDailySummaryV2Scalar`, `userDailySummaryV2AverageScalar` | `startDate, endDate` | daily summary cards |
| `userGoalsScalar` | none | goals |
| `vo2MaxScalar` | `startDate, endDate[, sport]` | VO2 max card |
| `weightScalar` | `startDate, endDate` | weight card |
| `workoutScheduleSummariesScalar` | `startDate, endDate` | workouts card |

## Query texts

```graphql
query{epochChartScalar(date:"${date}", include:["steps"])}
query{trainingStatusDailyScalar(calendarDate:"${date}")}
query{latestWeightScalar(asOfDate:"${date}")}
query{trainingStatusWeeklyScalar(startDate:"${start}", endDate:"${end}", displayName:"${displayName}")}
query{menstrualCycleScalar(date:"${date}")}
query { adhocChallengePendingInviteScalar }
query{enduranceScoreScalar(startDate:"${start}", endDate:"${end}", aggregation:"weekly")}
query { expeditionsChallengesScalar }
query { badgeChallengesScalar }
query { adhocChallengesScalar }
query{vo2MaxScalar(startDate:"${start}", endDate:"${end}", sport:"${sport}")}
query{vo2MaxScalar(startDate:"${start}", endDate:"${end}")}
query{activityTrendsScalar(activityType:"${activityType}",date:"${date}")}
query{myDayCardEventsScalar(timeZone:"GMT", date:"${date}")}
query{latestFitnessAgeScalar(asOfDate:"${date}")}
query{trainingReadinessRangeScalar(startDate:"${start}", endDate:"${end}")}
query{workoutScheduleSummariesScalar(startDate:"${start}", endDate:"${end}")}
query{searchActivitiesScalar(start:${start}, limit:${limit}, excludedActivitySubTypes: ["assistance"])}
query{dailyEventsScalar(date:"${date}")}
query{criticalSwimSpeedScalar(startDate:"${start}", endDate:"${end}")}
query{activityStatsScalar(aggregation:"${aggregation}", startDate:"${start}", endDate:"${end}", metrics:["duration","distance"], groupByParentActivityType:false, standardizedUnits: true)}
query{activityStatsScalar(aggregation:"${aggregation}", startDate:"${start}", endDate:"${end}", metrics:["duration","distance"], activityType:["running","cycling","swimming","walking","multi_sport","fitness_equipment","para_sports"], groupByParentActivityType:true, standardizedUnits: true)}
query{hillScoreScalar(startDate:"${start}", endDate:"${end}", aggregation:"weekly")}
query{jetLagScalar(date:"${date}")}
query { pendingActivities { pendingActivities { pendingActivityUUID calendarDate startTimeLocal endTimeLocal startTimeGMT endTimeGMT averageHR calories duration activityTypePredictionKeys } } }
query{sleepScalar(date:"${date}", sleepOnly: false)}
query { lifestyleLoggingStats(startDate: "${date}", endDate: "${date}") { completionStats { calendarDate, totalTracking, completedTracking } } }
query { calorieSummaryDailyStats(startDate: "${start}", endDate: "${end}", currentDate: "${today}") { dailyNutritionContents { mealDate nutritionContent { calories carbs fat protein caloriesPercentage } nutritionGoals { calories carbs fat protein adjustedCalories adjustedCarbs adjustedFat adjustedProtein } } averageNutritionContents { calories carbs fat protein caloriesPercentage } } }
query { userGoalsScalar }
query{trainingPlanScalar(calendarDate:"${date}", lang:"${locale}", firstDayOfWeek:"${firstDayOfWeek}")}
query{userDailySummaryV2Scalar(startDate:"${start}", endDate:"${end}")}
query{spO2AcclimationScalar(date:"${date}")}
query { runningLactateThresholdScalar }
query{pregnancyScalar(date:"${date}")}
query{functionalThresholdPowerScalar(startDate:"${start}", endDate:"${end}", sports:"${sports}")}
query{golfScorecardScalar(startTimestampLocal:"${startLocal}", endTimestampLocal:"${endLocal}")}
query{activitiesScalar(displayName:"${displayName}", startTimestampLocal:"${startLocal}", endTimestampLocal:"${endLocal}", limit:${limit})}
query{heartRateVariabilityScalar(startDate:"${start}", endDate:"${end}")}
query { healthStatusSummary(calendarDate:"${date}") { calendarDate outliersCount createTimestampUTC updateTimestampUTC metrics { value baselineUpperLimit baselineLowerLimit status percentage feedbackKey type } } }
query{weightScalar(startDate:"${start}", endDate:"${end}")}
query{ menstrualCycleDetail(date:"${date}", todayDate:"${date}"){ daySummary { pregnancyCycle } dayLog { calendarDate, symptoms, moods, discharge, hasBabyMovement } } }
query{userDailySummaryV2AverageScalar(startDate:"${start}", endDate:"${end}")}
query{bloodPressureScalar(startDate:"${start}", endDate:"${end}")}
query{heatAltitudeAcclimationScalar(date:"${date}")}
query{powerToWeightScalar(date:"${date}", sports:"RUNNING")}
query { cyclingAbility(startDate: "${date}", endDate: "${date}") { latest { userProfilePk deviceId calendarDate timestamp primaryTrainingDevice aerobicEndurance aerobicCapacity anaerobicCapacity profileType profileTypeFeedback aerobicEnduranceFeedback aerobicCapacityFeedback anaerobicCapacityFeedback } } }
query { personalRecordsScalar }
query { runningEconomy(startDate: "${start}",endDate: "${end}") { latest { calendarDate score classification } weeklyAggregates { startDate endDate score classification } } }
query{sleepSummariesScalar(startDate:"${start}", endDate:"${end}")}
query{trainingLoadBalanceScalar(calendarDate:"${date}", fullHistoryScan:true)}
query { runningToleranceStats(startDate: "${today}", endDate: "${today}", aggregation: daily) { userProfilePK calendarDate acuteImpactLoad acuteDistance acuteTolerance } }
query{heartRateScalar(date:"${date}")}
query{healthSnapshotScalar(startDate:"${start}", endDate:"${end}")}
```

A second, unrelated GraphQL endpoint, `/gateway/graph-atp/graphql`, serves
Garmin Coach content (`Coaches`, `Videos`, `Articles`) and is not covered by
this library.
