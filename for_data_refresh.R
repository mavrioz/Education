library(tidyverse)
library(readxl)
library(ggplot2)
library(viridis)

deaths <- read_excel("CO_Quintiles_Request_Final_File.xlsx", sheet = "Table 1", skip = 3, n_max = 46)
deaths_baseline <- read_excel("Deprivation_2015_2019_final.xlsx", sheet = "Table 1", skip = 4, n_max = 5)
deaths <- deaths[-1,]
deaths_March <- deaths %>% select(`Cause of death`,Sex,Quintile,`...6`,`...8`,`...9`)
colnames(deaths_March) <- c("cause","gender","quintile","death_rate","lower_CI","upper_CI") 
deaths_March <- deaths_March %>% mutate(month="March")
deaths_April <- deaths %>% select(`Cause of death`,Sex,Quintile,`...12`,`...14`,`...15`)
colnames(deaths_April) <- c("cause","gender","quintile","death_rate","lower_CI","upper_CI")
deaths_April <- deaths_April %>% mutate(month="April")
deaths_May <- deaths %>% select(`Cause of death`,Sex,Quintile,`...18`,`...20`,`...21`)
colnames(deaths_May) <- c("cause","gender","quintile","death_rate","lower_CI","upper_CI")
deaths_May <- deaths_May %>% mutate(month="May")
deaths_June <- deaths %>% select(`Cause of death`,Sex,Quintile,`...24`,`...26`,`...27`)
colnames(deaths_June) <- c("cause","gender","quintile","death_rate","lower_CI","upper_CI")
deaths_June <- deaths_June %>% mutate(month="June")
deaths_July <- deaths %>% select(`Cause of death`,Sex,Quintile,`...30`,`...32`,`...33`)
colnames(deaths_July) <- c("cause","gender","quintile","death_rate","lower_CI","upper_CI")
deaths_July <- deaths_July %>% mutate(month="July")

deaths <- rbind(deaths_March,deaths_April)
deaths <- rbind(deaths,deaths_May)
deaths <- rbind(deaths,deaths_June)
deaths <- rbind(deaths,deaths_July)

deaths$month <- factor(deaths$month, levels = (c("March","April","May","June","July")))
deaths$death_rate <- as.numeric(deaths$death_rate)
deaths$lower_CI <- as.numeric(deaths$lower_CI)
deaths$upper_CI <- as.numeric(deaths$upper_CI)

deaths_persons_covid <- deaths %>% filter(gender == "Persons"& cause=="COVID-19")

###### CLEAN UP DEATHS BASELINE FILE
deaths_baseline_March <- deaths_baseline %>% select(`...1`,`Rate...3`,`Lower...4`,`Upper...5`)
colnames(deaths_baseline_March) <- c("quintile","death_rate","lower_CI","upper_CI") 
deaths_baseline_March <- deaths_baseline_March %>% mutate(month="March")
deaths_baseline_April <- deaths_baseline %>% select(`...1`,`Rate...7`,`Lower...8`,`Upper...9`)
colnames(deaths_baseline_April) <- c("quintile","death_rate","lower_CI","upper_CI")
deaths_baseline_April <- deaths_baseline_April %>% mutate(month="April")
deaths_baseline_May <- deaths_baseline %>% select(`...1`,`Rate...11`,`Lower...12`,`Upper...13`)
colnames(deaths_baseline_May) <- c("quintile","death_rate","lower_CI","upper_CI")
deaths_baseline_May <- deaths_baseline_May %>% mutate(month="May")
deaths_baseline_June <- deaths_baseline %>% select(`...1`,`Rate...15`,`Lower...16`,`Upper...17`)
colnames(deaths_baseline_June) <- c("quintile","death_rate","lower_CI","upper_CI")
deaths_baseline_June <- deaths_baseline_June %>% mutate(month="June")

deaths_baseline <- rbind(deaths_baseline_March,deaths_baseline_April)
deaths_baseline <- rbind(deaths_baseline,deaths_baseline_May)
deaths_baseline <- rbind(deaths_baseline,deaths_baseline_June)

deaths_baseline$month <- factor(deaths_baseline$month, levels = (c("March","April","May","June")))#,"July")))

deaths_baseline$death_rate <- as.numeric(deaths_baseline$death_rate)
deaths_baseline$lower_CI <- as.numeric(deaths_baseline$lower_CI)
deaths_baseline$upper_CI <- as.numeric(deaths_baseline$upper_CI)

##### Combine 2 deaths files
deaths1 <- deaths_persons_covid %>% select(-cause,-gender)
deaths_baseline <- deaths_baseline %>% group_by(month) %>% mutate(
  variation = (death_rate - min(death_rate))/min(death_rate),
  variation_upper = (upper_CI - min(upper_CI))/min(upper_CI),
  variation_lower = (lower_CI - min(lower_CI))/min(lower_CI)) %>% 
  ungroup()
death_factors <- deaths_baseline %>% group_by(quintile) %>% summarise(
  mean_uplift=mean(variation),
  mean_uplift_upper=mean(variation_upper),
  mean_uplift_lower=mean(variation_lower)
) %>% ungroup()

deaths1 <- deaths1 %>% group_by(month) %>% mutate(
  predicted = (case_when(
    quintile == "1 (most deprived)" ~ min(death_rate)*(1+death_factors$mean_uplift[1]),
    quintile == "2" ~ min(death_rate)*(1+death_factors$mean_uplift[2]),
    quintile == "3" ~ min(death_rate)*(1+death_factors$mean_uplift[3]),
    quintile == "4" ~ min(death_rate)*(1+death_factors$mean_uplift[4]),
    quintile == "5 (least deprived)" ~ min(death_rate)*(1+death_factors$mean_uplift[5]))),
  predicted_lower =(case_when(
    quintile == "1 (most deprived)" ~ min(lower_CI)*(1+death_factors$mean_uplift_lower[1]),
    quintile == "2" ~ min(lower_CI)*(1+death_factors$mean_uplift_lower[2]),
    quintile == "3" ~ min(lower_CI)*(1+death_factors$mean_uplift_lower[3]),
    quintile == "4" ~ min(lower_CI)*(1+death_factors$mean_uplift_lower[4]),
    quintile == "5 (least deprived)" ~ min(lower_CI)*(1+death_factors$mean_uplift_lower[5]))),
  predicted_upper =(case_when(
    quintile == "1 (most deprived)" ~ min(upper_CI)*(1+death_factors$mean_uplift_upper[1]),
    quintile == "2" ~ min(upper_CI)*(1+death_factors$mean_uplift_upper[2]),
    quintile == "3" ~ min(upper_CI)*(1+death_factors$mean_uplift_upper[3]),
    quintile == "4" ~ min(upper_CI)*(1+death_factors$mean_uplift_upper[4]),
    quintile == "5 (least deprived)" ~ min(upper_CI)*(1+death_factors$mean_uplift_upper[5])))	
) %>% ungroup()

# Plot

pal <- viridisLite::viridis(5)
annotationsDF <- data.frame(
  x1 = c(5, 5),
  y1 = c(123, 102),
  text = c(
    "Quintile 1: expected", "Quintile 2: expected"
  )
)
s <- ggplot() +geom_line(data = deaths1,aes(x=month,y=death_rate,group=quintile)) + theme_classic() + 
  geom_ribbon(data = deaths1,aes(x=month,ymin=lower_CI, ymax=upper_CI, fill=quintile,group=quintile)) +
  labs(y="Age-standardised mortality rate per 100,000",x="", title = "Cumulative COVID-19 death rate by deprivation quintile")+

  geom_ribbon(data = deaths1, aes(x=month,ymin=predicted_lower, ymax=predicted_upper, fill=quintile,group=quintile), alpha=0.2) +
  scale_fill_viridis_d(option="B",direction=1) +
  geom_text(data=annotationsDF,aes(x=x1,y=y1,label=text),size=3) +
  annotate(
    geom = "curve", x = 4.65, y = 102, xend = 4.48, yend = 98, 
    curvature = .6, arrow = arrow(length = unit(2, "mm"))
  ) +
  annotate(
    geom = "curve", x = 4.65, y = 123, xend = 4.48, yend = 119, 
    curvature = .6, arrow = arrow(length = unit(2, "mm"))
  )

s

#### For image
#ggsave("COVID-19 deaths by quintile with baseline.jpeg",s)

#### For dashboard
#write_csv(deaths1,"for dashboard.csv")
q1 <- deaths1 %>% filter(quintile=="1 (most deprived)") %>% select(month,death_rate,lower_CI,upper_CI)
colnames(q1) <- c("month", "q1_death_rate", "q1_lower_CI", "q1_upper_CI")
q2 <- deaths1 %>% filter(quintile=="2") %>% select(month,death_rate,lower_CI,upper_CI)
colnames(q2) <- c("month", "q2_death_rate", "q2_lower_CI", "q2_upper_CI")
q3 <- deaths1 %>% filter(quintile=="3") %>% select(month,death_rate,lower_CI,upper_CI)
colnames(q3) <- c("month", "q3_death_rate", "q3_lower_CI", "q3_upper_CI")
q4 <- deaths1 %>% filter(quintile=="4") %>% select(month,death_rate,lower_CI,upper_CI)
colnames(q4) <- c("month", "q4_death_rate", "q4_lower_CI", "q4_upper_CI")
q5 <- deaths1 %>% filter(quintile=="5 (least deprived)") %>% select(month,death_rate,lower_CI,upper_CI)
colnames(q5) <- c("month", "q5_death_rate", "q5_lower_CI", "q5_upper_CI")
q1_pred <- deaths1 %>% filter(quintile=="1 (most deprived)") %>% select(month,predicted,predicted_lower,predicted_upper)
colnames(q1_pred) <- c("month", "q1_p_death_rate", "q1_p_lower_CI", "q1_p_upper_CI")
q2_pred <- deaths1 %>% filter(quintile=="2") %>% select(month,predicted,predicted_lower,predicted_upper)
colnames(q2_pred) <- c("month", "q2_p_death_rate", "q2_p_lower_CI", "q2_p_upper_CI")

output <- left_join(q1,q2)
output <- left_join(output,q3)
output <- left_join(output,q4)
output <- left_join(output,q5)
output <- left_join(output,q1_pred)
output <- left_join(output,q2_pred)