#!/usr/bin/perl

use strict;

my $region="us-west-2";
my $stackUrl="https://s3-us-west-2.amazonaws.com/jenkins-8k/test.json";
my $stackParameters="";
my @Parameters=();
my $parameterFile="/home/ec2-user/parameter";
my $instanceName="Devops";
my $finalStatus=undef;

ValidateInput();
ValidateTemplate();
CreateStack($parameterFile);


sub ValidateInput
{
	print "----------------------------------------------\n";
	if($stackUrl =~ "null" or ! -e $parameterFile )
	{
		print "No Stack URL presented or Parameter file is missing, exiting this step\n";
		exit(0);
	}
}	
sub ValidateTemplate
{ 
	print "------------------------------------------------\n";
	my $command = "aws cloudformation validate-template --template-url $stackUrl 2>&1"; 
	print "Executing command: \[ $command \]\n";
	my @results =`$command`;   
	foreach my $result (@results)
	{     
		chomp $result;
		if ($result =~ "ValidationError")     
		{   
			print "The CFT is not a well formatted Json or Yaml. Aborting stack creation!! \n";    
			print "$result\n";
			exit(1); 
		} 
	} 
	print "The template passed validation test, proceeding with next steps\n";
}

sub CreateStack
{
	my $parameterFile=$_[0];
	my $stackCreationStarted = 0;

	print "----------------------------------------------\n";
	print "Verifying Parameter string for creation...\n";

	open(FP,$parameterFile) or die "Can't read $parameterFile : $!\n";
	my @parameterList=<FP>;
	close(FP);

	my $command=undef;

	if ( ( my $len = @parameterList ) == 0 )
	{
		print "No Parameters given to run the stack. Running stack without parameters\n";
		$command="aws cloudformation create-stack --stack-name $instanceName --template-url $stackUrl --region $region 2>&1";
	}
	else
	{
		CreateParameterString(@parameterList);
		print "In else\n";
		$command="aws cloudformation create-stack --stack-name $instanceName --template-url $stackUrl --parameters $stackParameters --region $region 2>&1";
	}

	print "Creating the stack\n";
	print "Executing command \[$command]\n";
	my @results = `$command`;
	if (@results)
	{
		for my $result (@results)
		{
			chomp $result;
			print "$result\n";

			if ( $result =~ "arn" )
			{
				$stackCreationStarted=1;
			}
			if ($result =~ "An error occured" or $result =~ "Parameter validation failed")
			{
				DebugErrors();
			}
		}
	}
	if ($stackCreationStarted == 1)
	{
		ValidateStack();
	}
	else
	{
		print "Stack Failed to produce ARN, Likely failed \n";
	}

}
sub ValidateStack
{
	my $limit=120;
	my $sleep=15;
	my $counter=0;
	my $currentStatus=undef;
	my $finalStatus=undef;

#CREATE_COMPLETE;
#CREATE_FAILED;
#CREATE_IN_PROGRESS
#DELETE_COMPLETE
#DELETE_IN_PROGRESS
#ROLLBACK_COMPLETE
#ROLLBACK_FAILED
#ROLLBACK_IN_PROGRESS
#UPDATE_COMPLETE
#UPDATE_COMPLETE_CLEANUP_IN_PROGRESS
#UPDATE_IN_PROGRESS
#UPDATE_ROLLBACK_COMPLETE
#UPDATE_ROLLBACK_CLEANUP_IN_PROGRESS
#UPDATE_ROLLBACK_FAILED
#UPDATE_ROLLBACK_IN_PROGRESS

	print "Stack was generated . Sleeping for few seconds to validate it\n";
	my $command="sleep 15 2>&1";
	my @results=`$command` ;

	if (@results)
	{
		for my $result (@results)
		{
			chomp$result;
		}
	}

	print "----------------------------------------------\n";
	print "Need to start a loop to watch the stack be built out ...\n";
	print "Checking:\[$limit\] times at:\[$sleep\] second interval\n";
	print "This could take likely a good amount of time...\n";
	print "-----Creation In Progress----\n";

	my $processString = undef;
	while ($counter < $limit)
	{
		$counter++;
		my $command="aws cloudformation describe-stacks --stack-name $instanceName --region $region | grep StackStatus 2>&1";
		print "Command is $command\n";
		my @results= `$command`;
		if (@results)
		{
			for my $result (@results)
			{
				chomp $result;
				print "Result : $result\n";
				if ( $result =~ "StackStatus" )
				{
					my ($var1,$var2,$var3,$var4,$var5)=split("\"",$result);
					$currentStatus = $var4;
					if ($currentStatus =~ "IN_PROGRESS")
					{
						if( $currentStatus =~ "CREATE_IN_PROGRESS")
						{
							$processString.=".";
							print $processString;
						}
						elsif($currentStatus =~ "DELETE_IN_PROGRESS" or $currentStatus =~ "ROLLBACK_IN_PROGRESS")
						{
							print "CReation of stack failed and is backing out\n";
							$finalStatus="Failed";
							DebugErrors();
						}
					}	
					else
					{
						if ($currentStatus =~ "CREATE_COMPLETE")
						{
							print "\n";
							$finalStatus="Success";
							print "Stack created successfully\n";
							print "Need to go get the keys and values\n";
							$counter = $limit;
							GetKeyValues();
						}
						elsif($currentStatus =~ "CREATE_FAILED" or $currentStatus =~ "ROLLBACK_FAILED" or $currentStatus =~ "DELETE_FAILED" or $currentStatus =~ "ROLLBACK_COMPLETE" )
						{
							print "Creation has failed and the current status is $currentStatus\n";
							$finalStatus="Failed";
							DebugErrors();
						}
					}
				}
			}

			my $command="sleep $sleep 2>&1";
			my @results=`$command`;

			if (@results)
			{
				for my $result (@results)
				{
					chomp$result;
				}
			}
		}
		else
		{
			print "---------------------------------------------------\n";
			print "No Validresponse from AWS have to assume that describe failed and stack is dead\n";
			DebugErrors();
		}

	}
	if ( $finalStatus =~ "Success")
	{
		print "-------------------------------------------------\n";
		print "We have built new env and grabbed env var...we should good to go\n";
	}
	else
	{
		print "-------------------------------------------------\n";
		print "We made it out of the loop in a non success route..not sure how\n";
		DebugErrors();
	}	
}
sub GetKeyValues
{
	my @KeyValuePairs=();
	print "-------------------------------------------------\n";
	print "Grabbing all key values we can from \[$instanceName\]\n";

	my $command="aws cloudformation describe-stacks --stack-name $instanceName --region $region| grep Output 2>&1";
	my @results=`$command`;
	if (@results)
	{
		my $key= undef;
		my $value=undef;
		for my $result (@results)
		{
			chomp $result;
			if ( $result =~ "Outputs" )
			{
				print "\n";
			}
			elsif ( $result =~ "OutputKey" )
			{
				print "-------------------------------------------------\n";
				my ($var1,$var2,$var3,$var4,$var5)=split("\"",$result);
				$key=$var4;
				print "key : \[$key\]\n";
			}
			elsif ( $result =~ "OutputValue" )
			{
				print "-------------------------------------------------\n";
				my ($var1,$var2,$var3,$var4,$var5)=split("\"",$result);
				$value=$var4;
				print "Value : \[$value\]\n";
				if(length($key) > 1)
				{
					my $string = $key . "," . $value;
					push(@KeyValuePairs,$string);
					($key,$value)=undef;
				}
				else
				{
					print "Warn : Value without key this is likely bad ...\nValues may be off";
				}

			}
		}
	}
	foreach my $pair (@KeyValuePairs)
	{
		print "-----------------------------------------------------\n";
		my ($key,$value)=split("\,",$pair,2);
		print "key : \[$key\]\n value : \[$value\]\n";
	}
}

sub CreateParameterString
{
	my @parameterList=@_;
	foreach my $Parameter (@parameterList)
	{
		chomp $Parameter;
		if ( $Parameter =~ "ParameterKey" and $Parameter =~ "ParameterValue" )
		{
			print "It appears string is  formated... Moving on \n";
			$stackParameters.="$Parameter ";
		}
		else
		{
			print "Please add parameters as below\ne.g ParameterKey=\"InstanceIAMRole\",ParameterValue=\"Jenkins\"\n Exiting here!!!\n";
			exit (0);
		}
	}
}

sub DebugErrors
{
	print "##################################################\n";
	print "########### Step Has Faialed ####################\n";
	print "########### End Transmission ####################\n";
	print "########### Exiting Now ########################\n";
	print "##################################################\n";

	exit(1);
}

