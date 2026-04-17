import { Dog } from './dog.model';

export interface DogSummary {
  dog: Dog;
  eligible_for_team_builder: boolean;
  eligibility_reasons: string[];
  risk_level: string;
  usage_level?: string | null;
}