/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import "MGProfitPrint.h"
#import "MGConst.h"

@implementation MGProfitPrint
- (NSArray *)unresizableColumns
{
    return [NSArray arrayWithObjects:@"current",@"last",nil];
}

-(void)setUpWithPrintInfo:(NSPrintInfo *)pi
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    graphVisible = [ud boolForKey:ProfitGraphVisible];
    pieVisible = [ud boolForKey:IncomeExpensePieChartVisible];
    [super setUpWithPrintInfo:pi];
}
@end